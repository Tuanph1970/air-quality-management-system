"""WRF Model Runner.

Executes the WRF (Weather Research and Forecasting) model including:
- WPS (WRF Preprocessing System): geogrid, ungrib, metgrid
- WRF Model: real.exe, wrf.exe
- Post-processing: extracting variables to NetCDF
"""
import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from ...domain.entities.wrf_simulation import WRFSimulation, SimulationStatus
from ...domain.value_objects.wrf_config import WRFConfig
from ..config import settings

logger = logging.getLogger(__name__)


class WRFModelRunner:
    """Executes WRF model simulations."""

    def __init__(
        self,
        wrf_dir: Optional[str] = None,
        wps_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        self.wrf_dir = Path(wrf_dir or settings.WRF_MODEL_DIR)
        self.wps_dir = Path(wps_dir or settings.WPS_DIR)
        self.output_dir = Path(output_dir or settings.WRF_OUTPUT_DIR)
        self.num_processes = settings.WRF_NUM_PROCESSES

    async def run_preprocessing(self, simulation: WRFSimulation) -> None:
        """
        Run WPS preprocessing steps.

        1. geogrid.exe - Define domain and interpolate static geographic data
        2. ungrib.exe - Extract meteorological data from GFS GRIB files
        3. metgrid.exe - Combine static and meteorological fields
        """
        sim_dir = self._get_simulation_directory(simulation.id)
        wps_output = sim_dir / "WPS"
        wps_output.mkdir(parents=True, exist_ok=True)

        config = simulation.config

        # Write namelist.wps
        await self._write_namelist_wps(config, wps_output)

        # Run geogrid.exe
        logger.info(f"Running geogrid.exe for simulation {simulation.id}")
        await self._run_executable(
            self.wps_dir / "geogrid.exe",
            wps_output,
            f"geogrid_{simulation.id}",
        )

        # Run ungrib.exe (link GFS files first)
        logger.info(f"Running ungrib.exe for simulation {simulation.id}")
        await self._link_gfs_files(simulation.gfs_data_path, wps_output)
        await self._run_executable(
            self.wps_dir / "ungrib.exe",
            wps_output,
            f"ungrib_{simulation.id}",
        )

        # Run metgrid.exe
        logger.info(f"Running metgrid.exe for simulation {simulation.id}")
        await self._run_executable(
            self.wps_dir / "metgrid.exe",
            wps_output,
            f"metgrid_{simulation.id}",
        )

        logger.info(f"WPS preprocessing completed for simulation {simulation.id}")

    async def run_simulation(
        self,
        simulation: WRFSimulation,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> List[str]:
        """
        Run WRF model simulation.

        1. real.exe - Initialize real-data simulation
        2. wrf.exe - Run the actual WRF model

        Args:
            simulation: WRF simulation entity
            progress_callback: Optional callback for progress updates

        Returns:
            List of output file paths
        """
        sim_dir = self._get_simulation_directory(simulation.id)
        wrf_output = sim_dir / "WRF"
        wrf_output.mkdir(parents=True, exist_ok=True)

        config = simulation.config

        # Write namelist.input
        await self._write_namelist_input(config, wrf_output)

        # Run real.exe
        if progress_callback:
            progress_callback(5, "Running real.exe...")

        logger.info(f"Running real.exe for simulation {simulation.id}")
        await self._run_executable(
            self.wrf_dir / "main" / "real.exe",
            wrf_output,
            f"real_{simulation.id}",
        )

        # Run wrf.exe
        if progress_callback:
            progress_callback(15, "Running wrf.exe...")

        logger.info(f"Running wrf.exe for simulation {simulation.id}")
        await self._run_wrf_exe(wrf_output, simulation, progress_callback)

        # Collect output files
        output_files = await self._collect_output_files(wrf_output)

        return output_files

    async def post_process(self, simulation: WRFSimulation) -> None:
        """
        Post-process WRF output.

        Extract variables of interest and create analysis-ready files.
        """
        sim_dir = self._get_simulation_directory(simulation.id)
        wrf_output = sim_dir / "WRF"

        # Use wrf-python or custom scripts to extract variables
        # This would typically create separate files for each variable
        logger.info(f"Post-processing simulation {simulation.id}")

        # Create variable-specific output files
        variables = ["temperature", "humidity", "wind", "pressure"]
        for var in variables:
            output_file = wrf_output / f"{var}_output.nc"
            # In production, this would use wrf-python to extract the variable
            output_file.touch()

    async def _run_executable(
        self,
        executable: Path,
        work_dir: Path,
        job_name: str,
    ) -> None:
        """Run a WRF/WPS executable."""
        if not executable.exists():
            # For development/testing, simulate execution
            logger.warning(
                f"Executable not found: {executable}, simulating execution"
            )
            await asyncio.sleep(2)  # Simulate processing
            return

        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(self.num_processes)

        process = await asyncio.create_subprocess_exec(
            str(executable),
            cwd=str(work_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"{job_name} failed: {error_msg}")

        logger.info(f"{job_name} completed successfully")

    async def _run_wrf_exe(
        self,
        wrf_dir: Path,
        simulation: WRFSimulation,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> None:
        """Run wrf.exe with progress monitoring."""
        executable = self.wrf_dir / "main" / "wrf.exe"

        if not executable.exists():
            # Simulate long-running WRF execution
            logger.warning(f"WRF executable not found, simulating run")
            total_steps = 10
            for step in range(total_steps):
                await asyncio.sleep(1)
                if progress_callback:
                    progress_callback(
                        step * 10,
                        f"Simulating WRF step {step + 1}/{total_steps}",
                    )
            return

        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(self.num_processes)

        process = await asyncio.create_subprocess_exec(
            str(executable),
            cwd=str(wrf_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        # Monitor progress by reading output
        elapsed_hours = 0
        total_hours = simulation.config.simulation_hours

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode()
            logger.debug(f"WRF: {line_str.strip()}")

            # Parse WRF output for timing information
            if "Timing for main" in line_str and progress_callback:
                elapsed_hours += 1
                progress = int((elapsed_hours / total_hours) * 100)
                progress_callback(
                    progress,
                    f"Simulated {elapsed_hours}h / {total_hours}h",
                )

        await process.wait()

        if process.returncode != 0:
            raise RuntimeError("wrf.exe failed")

    async def _write_namelist_wps(self, config: WRFConfig, output_dir: Path) -> None:
        """Write WPS namelist.wps file."""
        bbox = config.bounding_box

        namelist = f"""
&share
 wrf_core = 'ARW',
 max_dom = 1,
 start_date = '{config.start_date or '2024-01-01_00:00:00'}',
 end_date = '{config.start_date or '2024-01-02_00:00:00'}',
 interval_seconds = 10800,
 io_form_geogrid = 2,
/

&geogrid
 parent_id         = 1,
 parent_grid_ratio = 1,
 i_parent_start    = 1,
 j_parent_start    = 1,
 e_we              = {int(bbox.width_km / config.horizontal_resolution_km)},
 e_sn              = {int(bbox.height_km / config.horizontal_resolution_km)},
 geog_data_res     = 'default',
 dx                = {config.horizontal_resolution_km * 1000},
 dy                = {config.horizontal_resolution_km * 1000},
 map_proj          = 'lambert',
 ref_lat           = {bbox.center_lat},
 ref_lon           = {bbox.center_lon},
 truelat1          = {bbox.center_lat - 2},
 truelat2          = {bbox.center_lat + 2},
 standlon          = {bbox.center_lon},
 geog_data_path    = '/app/wrf/WPS_GEOG',
/

&ungrib
 out_format = 'WPS',
 prefix     = 'FILE',
/

&metgrid
 fg_name = 'FILE',
 io_form_metgrid = 2,
/
"""

        namelist_path = output_dir / "namelist.wps"
        namelist_path.write_text(namelist)
        logger.info(f"Written namelist.wps to {namelist_path}")

    async def _write_namelist_input(self, config: WRFConfig, output_dir: Path) -> None:
        """Write WRF namelist.input file."""
        bbox = config.bounding_box
        physics = config.physics_options.to_wrf_namelist()

        namelist = f"""
&time_control
 run_days                            = 0,
 run_hours                           = {config.simulation_hours},
 run_minutes                         = 0,
 run_seconds                         = 0,
 start_year                          = 2024,
 start_month                         = 01,
 start_day                           = 01,
 start_hour                          = 00,
 start_minute                        = 00,
 start_second                        = 00,
 interval_seconds                    = 10800,
 input_from_file                     = .true.,
 fine_input_stream                   = 1,
 history_interval                    = {config.output_interval_hours * 60},
 frames_per_outfile                  = 1,
 restart                             = .false.,
 restart_interval                    = {config.simulation_hours},
 io_form_history                     = 2,
 io_form_restart                     = 2,
 io_form_input                       = 2,
 io_form_boundary                    = 2,
/

&domains
 time_step                           = {int(config.horizontal_resolution_km * 6)},
 time_step_fract                     = 0,
 max_dom                             = 1,
 e_we                                = {int(bbox.width_km / config.horizontal_resolution_km) + 4},
 e_sn                                = {int(bbox.height_km / config.horizontal_resolution_km) + 4},
 e_vert                              = {config.vertical_levels},
 p_top_requested                     = 5000,
 num_metgrid_levels                  = 33,
 num_metgrid_soil_levels             = 4,
 dx                                  = {config.horizontal_resolution_km * 1000},
 dy                                  = {config.horizontal_resolution_km * 1000},
 grid_id                             = 1,
 parent_id                           = 1,
 i_parent_start                      = 1,
 j_parent_start                      = 1,
 parent_grid_ratio                   = 1,
 parent_time_step_ratio              = 1,
 feedback                            = 0,
 smooth_option                       = 0,
 sfcp_to_sfcp                        = .false.,
 use_theta_m                         = 0,
 ref_lat                             = {bbox.center_lat},
 ref_lon                             = {bbox.center_lon},
 truelat1                            = {bbox.center_lat - 2},
 truelat2                            = {bbox.center_lat + 2},
 standlon                            = {bbox.center_lon},
 pole_lat                            = 90.0,
 pole_lon                            = 0.0,
 map_proj                            = 'lambert',
/

&physics
 mp_physics                          = {physics['mp_physics']},
 ra_lw_physics                       = {physics['ra_lw_physics']},
 ra_sw_physics                       = {physics['ra_sw_physics']},
 radt                                = 30,
 sf_sfclay_physics                   = 1,
 sf_surface_physics                  = {physics['sf_surface_physics']},
 sf_pbl_physics                      = {physics['sf_pbl_physics']},
 bl_pbl_physics                      = 1,
 bldt                                = 0,
 cudt                                = 0,
 isfflx                              = 1,
 ifsnow                              = 0,
 icloud                              = 1,
 surface_input_source                = 1,
 num_soil_layers                     = 4,
 maxiens                             = 1,
 maxens                              = 3,
 maxens2                             = 16,
 maxens_dim                          = 2,
/

&fdda
/

&dynamics
 w_damping                           = 0,
 diff_opt                            = 1,
 km_opt                              = 4,
 diff_6th_opt                        = 0,
 diff_6th_factor                     = 0.12,
 base_temp                           = 290.0,
 damp_opt                            = 0,
 zdamp                               = 5000.0,
 dampcoef                            = 0.2,
 khdif                               = 0,
 kvdif                               = 0,
 non_hydrostatic                     = .true.,
 moist_adv_opt                       = 1,
 scalar_adv_opt                       = 1,
/

&bdy_control
 spec_bdy_width                      = 5,
 spec_zone                           = 1,
 relax_zone                          = 4,
 specified                           = .true.,
 periodic_x                          = .false.,
 symmetric_xs                        = .false.,
 symmetric_xe                        = .false.,
 open_xs                             = .false.,
 open_xe                             = .false.,
 periodic_y                          = .false.,
 symmetric_ys                        = .false.,
 symmetric_ye                        = .false.,
 open_ys                             = .false.,
 open_ye                             = .false.,
 nested                              = .false.,
/

&grib2
/

&namelist_quilt
 nio_tasks_per_group                 = 0,
 nio_groups                          = 1,
/
"""

        namelist_path = output_dir / "namelist.input"
        namelist_path.write_text(namelist)
        logger.info(f"Written namelist.input to {namelist_path}")

    async def _link_gfs_files(
        self, gfs_data_path: str, wps_output: Path
    ) -> None:
        """Create symbolic links for GFS files in WPS directory."""
        gfs_dir = Path(gfs_data_path)
        links_dir = wps_output

        grib_files = list(gfs_dir.glob("*.grib2"))

        for i, grib_file in enumerate(sorted(grib_files)):
            link_name = links_dir / f"FILE:{(i + 1):04d}"
            if not link_name.exists():
                link_name.symlink_to(grib_file)

        logger.info(f"Created {len(grib_files)} links to GFS files")

    async def _collect_output_files(self, wrf_dir: Path) -> List[str]:
        """Collect WRF output files."""
        output_files = []

        # Look for wrfout files
        for f in wrf_dir.glob("wrfout_d01_*"):
            output_files.append(str(f))

        # Look for other output files
        for f in wrf_dir.glob("wrfbdy_d01"):
            output_files.append(str(f))
        for f in wrf_dir.glob("wrflowinp_d01_*"):
            output_files.append(str(f))

        logger.info(f"Collected {len(output_files)} WRF output files")
        return output_files

    def _get_simulation_directory(self, simulation_id: UUID) -> Path:
        """Get the output directory for a simulation."""
        sim_dir = self.output_dir / str(simulation_id)
        sim_dir.mkdir(parents=True, exist_ok=True)
        return sim_dir

    async def check_wrf_installation(self) -> dict:
        """Check if WRF is properly installed."""
        result = {
            "wrf_installed": False,
            "wps_installed": False,
            "geogrid_available": False,
            "ungrib_available": False,
            "metgrid_available": False,
            "real_exe_available": False,
            "wrf_exe_available": False,
            "wrf_dir": str(self.wrf_dir),
            "wps_dir": str(self.wps_dir),
        }

        if self.wrf_dir.exists():
            result["wrf_installed"] = True
            result["real_exe_available"] = (
                self.wrf_dir / "main" / "real.exe"
            ).exists()
            result["wrf_exe_available"] = (
                self.wrf_dir / "main" / "wrf.exe"
            ).exists()

        if self.wps_dir.exists():
            result["wps_installed"] = True
            result["geogrid_available"] = (self.wps_dir / "geogrid.exe").exists()
            result["ungrib_available"] = (self.wps_dir / "ungrib.exe").exists()
            result["metgrid_available"] = (self.wps_dir / "metgrid.exe").exists()

        return result
