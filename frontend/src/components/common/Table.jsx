import PropTypes from 'prop-types';
import LoadingSpinner from './LoadingSpinner';
import EmptyState from './EmptyState';

function Table({ columns, data, isLoading = false, emptyIcon, emptyTitle, emptyDescription, onRowClick, className = '' }) {
  if (isLoading) {
    return <LoadingSpinner className="py-16" size="lg" />;
  }

  if (!data || data.length === 0) {
    return (
      <EmptyState icon={emptyIcon} title={emptyTitle || 'No data'} description={emptyDescription} />
    );
  }

  return (
    <div className={`card !p-0 overflow-hidden ${className}`}>
      <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIdx) => (
              <tr
                key={row.id || rowIdx}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={onRowClick ? 'cursor-pointer' : ''}
              >
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

Table.propTypes = {
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      width: PropTypes.string,
      render: PropTypes.func,
    })
  ).isRequired,
  data: PropTypes.array,
  isLoading: PropTypes.bool,
  emptyIcon: PropTypes.elementType,
  emptyTitle: PropTypes.string,
  emptyDescription: PropTypes.string,
  onRowClick: PropTypes.func,
  className: PropTypes.string,
};

export default Table;
