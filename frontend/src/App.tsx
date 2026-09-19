import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { useRoute } from './hooks/useRoute';
import { Dashboard } from './pages/Dashboard';
import { Plants } from './pages/Plants';
import { PlantDetails } from './pages/PlantDetails';
import { AnalyzePage } from './pages/AnalyzePage';
import { HistoryPage } from './pages/HistoryPage';
import { KnowledgeExplorer } from './pages/KnowledgeExplorer';
import { AnalysisReportPage } from './pages/AnalysisReportPage';
import { SettingsPage } from './pages/SettingsPage';
import { ServerGate } from './components/ServerGate';

function Router() {
  const { segments } = useRoute();
  const [first, second, third] = segments;

  if (!first) return <Dashboard />;
  if (first === 'plants' && second) return <PlantDetails plantId={Number(second)} key={second} />;
  if (first === 'plants') return <Plants />;
  if (first === 'analyze') return <AnalyzePage plantId={second ? Number(second) : undefined} key={second ?? 'new'} />;
  if (first === 'analysis' && second) return <AnalysisReportPage analysisId={Number(second)} key={second} />;
  if (first === 'history') return <HistoryPage />;
  if (first === 'knowledge') return <KnowledgeExplorer />;
  if (first === 'settings') return <SettingsPage />;
  return <Dashboard />;
}

export default function App() {
  return (
    <ServerGate>
      <Layout>
        <Router />
        <Toaster position="top-center" richColors />
      </Layout>
    </ServerGate>
  );
}
