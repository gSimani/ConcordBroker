import { useElementId } from '@/utils/generateElementId';

export default function PropertyPage() {
  const { generateId, generateTestId } = useElementId('property');

  return (
    <div id={generateId('main', 'container', 1)} data-testid={generateTestId('page', 'main')}>
      Property Page
    </div>
  );
}
