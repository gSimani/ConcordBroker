import * as React from "react"
import { cn } from "@/lib/utils"
import { generateElementId, generateTestId } from "@/utils/generateElementId"

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  id?: string;
}

const Card = React.forwardRef<
  HTMLDivElement,
  CardProps
>(({ className, id, ...props }, ref) => (
  <div
    ref={ref}
    id={id || generateElementId('ui', 'card', 'container', 1)}
    data-testid={generateTestId('card', 'container')}
    className={cn(
      "rounded-lg border bg-card text-card-foreground shadow-sm",
      className
    )}
    {...props}
  />
))
Card.displayName = "Card"

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  id?: string;
}

const CardHeader = React.forwardRef<
  HTMLDivElement,
  CardHeaderProps
>(({ className, id, ...props }, ref) => (
  <div
    ref={ref}
    id={id || generateElementId('ui', 'card', 'header', 1)}
    data-testid={generateTestId('card', 'header')}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn(
      "text-2xl font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {
  id?: string;
}

const CardContent = React.forwardRef<
  HTMLDivElement,
  CardContentProps
>(({ className, id, ...props }, ref) => (
  <div
    ref={ref}
    id={id || generateElementId('ui', 'card', 'content', 1)}
    data-testid={generateTestId('card', 'content')}
    className={cn("p-6 pt-0", className)}
    {...props}
  />
))
CardContent.displayName = "CardContent"

export { Card, CardHeader, CardTitle, CardDescription, CardContent }