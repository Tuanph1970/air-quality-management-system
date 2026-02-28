import { useState, useRef } from 'react';
import PropTypes from 'prop-types';
import { Upload, FileSpreadsheet, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { satelliteApi } from '../../services/satelliteApi';
import Modal from '../common/Modal';
import Button from '../common/Button';

const ExcelImportModal = ({ isOpen, onClose, onImportComplete }) => {
  const [file, setFile] = useState(null);
  const [importType, setImportType] = useState('historical_readings');
  const [validation, setValidation] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setValidation(null);
    setImportResult(null);

    // Validate file
    try {
      const result = await satelliteApi.validateExcel(selectedFile, importType);
      setValidation(result);
    } catch (error) {
      setValidation({ is_valid: false, errors: [error.message] });
    }
  };

  const handleImport = async () => {
    if (!file || !validation?.is_valid) return;

    setImporting(true);
    try {
      const result = await satelliteApi.importExcel(file, importType);
      setImportResult(result);
      onImportComplete?.(result);
    } catch (error) {
      setImportResult({ status: 'failed', errors: [error.message] });
    } finally {
      setImporting(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setValidation(null);
    setImportResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Import Excel Data">
      <div className="space-y-4">
        {/* Import Type Selection */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Data Type
          </label>
          <select
            value={importType}
            onChange={(e) => setImportType(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white"
          >
            <option value="historical_readings">Historical Air Quality Readings</option>
            <option value="factory_records">Factory Records</option>
          </select>
        </div>

        {/* File Upload */}
        <div
          className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center cursor-pointer hover:border-slate-500"
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".xlsx,.xls"
            onChange={handleFileSelect}
            className="hidden"
          />
          {file ? (
            <div className="flex items-center justify-center gap-2">
              <FileSpreadsheet className="text-green-400" size={24} />
              <span className="text-white">{file.name}</span>
            </div>
          ) : (
            <>
              <Upload className="mx-auto text-slate-400 mb-2" size={32} />
              <p className="text-slate-400">Click to upload Excel file</p>
              <p className="text-xs text-slate-500 mt-1">.xlsx or .xls</p>
            </>
          )}
        </div>

        {/* Validation Results */}
        {validation && (
          <div className={`p-4 rounded-lg ${validation.is_valid ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
            <div className="flex items-center gap-2 mb-2">
              {validation.is_valid ? (
                <CheckCircle className="text-green-400" size={20} />
              ) : (
                <XCircle className="text-red-400" size={20} />
              )}
              <span className="font-medium text-white">
                {validation.is_valid ? 'File Valid' : 'Validation Failed'}
              </span>
            </div>
            {validation.is_valid && (
              <p className="text-sm text-slate-300">
                {validation.row_count} rows found
              </p>
            )}
            {validation.errors?.map((error, i) => (
              <p key={i} className="text-sm text-red-400">{error}</p>
            ))}
            {validation.warnings?.map((warning, i) => (
              <p key={i} className="text-sm text-yellow-400 flex items-center gap-1">
                <AlertTriangle size={14} /> {warning}
              </p>
            ))}
          </div>
        )}

        {/* Import Result */}
        {importResult && (
          <div className={`p-4 rounded-lg ${importResult.status === 'completed' ? 'bg-green-900/30' : 'bg-red-900/30'}`}>
            <p className="font-medium text-white">
              {importResult.status === 'completed' 
                ? `Successfully imported ${importResult.processed_count} records`
                : 'Import failed'}
            </p>
            {importResult.error_count > 0 && (
              <p className="text-sm text-yellow-400">
                {importResult.error_count} errors
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-700">
          <Button variant="ghost" onClick={() => { resetForm(); onClose(); }}>
            Cancel
          </Button>
          <Button
            onClick={handleImport}
            disabled={!file || !validation?.is_valid || importing}
            loading={importing}
          >
            Import Data
          </Button>
        </div>
      </div>
    </Modal>
  );
};

ExcelImportModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onImportComplete: PropTypes.func
};

export default ExcelImportModal;
