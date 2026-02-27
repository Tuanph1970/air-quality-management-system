import { useState } from 'react';
import PropTypes from 'prop-types';
import { AlertTriangle } from 'lucide-react';
import Modal from '../common/Modal';
import Button from '../common/Button';

function SuspendModal({ isOpen, onClose, onConfirm, factoryName, isLoading = false }) {
  const [reason, setReason] = useState('');

  const handleConfirm = () => {
    if (reason.trim()) {
      onConfirm(reason.trim());
      setReason('');
    }
  };

  const handleClose = () => {
    setReason('');
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Suspend Factory Operations"
      footer={
        <>
          <Button variant="ghost" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            variant="danger"
            icon={AlertTriangle}
            onClick={handleConfirm}
            disabled={!reason.trim()}
            loading={isLoading}
          >
            Confirm Suspension
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <div className="flex items-start gap-3 p-4 rounded-xl bg-aqi-unhealthy/5 border border-aqi-unhealthy/20">
          <AlertTriangle className="w-5 h-5 text-aqi-unhealthy flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-aqi-unhealthy">Warning</p>
            <p className="text-xs text-[var(--color-text-muted)] mt-1">
              You are about to suspend operations for{' '}
              <span className="font-semibold text-[var(--color-text-primary)]">{factoryName}</span>.
              This action will halt all factory operations and trigger a notification to relevant parties.
            </p>
          </div>
        </div>

        <div>
          <label
            htmlFor="suspend-reason"
            className="block text-xs font-medium text-[var(--color-text-secondary)] mb-2"
          >
            Reason for suspension <span className="text-aqi-unhealthy">*</span>
          </label>
          <textarea
            id="suspend-reason"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Describe the reason for suspending this factory..."
            rows={4}
            className="input w-full resize-none"
          />
          <p className="text-[10px] text-[var(--color-text-muted)] mt-1.5">
            This reason will be recorded in the suspension history and included in notifications.
          </p>
        </div>
      </div>
    </Modal>
  );
}

SuspendModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  factoryName: PropTypes.string,
  isLoading: PropTypes.bool,
};

export default SuspendModal;
