import { cn } from "@/lib/utils"
import { generateElementId, generateTestId } from "@/utils/generateElementId"

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  id?: string;
}

function Skeleton({
  className,
  id,
  ...props
}: SkeletonProps) {
  return (
    <div
      id={id || generateElementId('ui', 'skeleton', 'container', 1)}
      data-testid={generateTestId('skeleton', 'container')}
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }