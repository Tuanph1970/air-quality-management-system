import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import Header from '../components/layout/Header';
import Button from '../components/common/Button';
import FactoryDetail from '../components/factories/FactoryDetail';
import LoadingSpinner from '../components/common/LoadingSpinner';
import EmptyState from '../components/common/EmptyState';
import { useFactory } from '../hooks/useFactories';

function FactoryDetailPage() {
  const { factoryId } = useParams();
  const navigate = useNavigate();
  const { factory, isLoading, error, suspendFactory, resumeFactory } = useFactory(factoryId);

  return (
    <>
      <Header
        title={factory?.name || 'Factory Details'}
        subtitle={factory?.registration_number || 'Loading...'}
      />

      <main className="p-6">
        <div className="mb-6">
          <Button
            variant="ghost"
            icon={ArrowLeft}
            onClick={() => navigate('/factories')}
            size="sm"
          >
            Back to Factories
          </Button>
        </div>

        {isLoading && !factory && (
          <LoadingSpinner className="py-20" size="lg" />
        )}

        {error && !factory && (
          <EmptyState
            title="Factory not found"
            description={error}
            action={
              <Button variant="secondary" onClick={() => navigate('/factories')}>
                View All Factories
              </Button>
            }
          />
        )}

        {factory && (
          <FactoryDetail
            factory={factory}
            onSuspend={suspendFactory}
            onResume={resumeFactory}
            isLoading={isLoading}
          />
        )}
      </main>
    </>
  );
}

export default FactoryDetailPage;
