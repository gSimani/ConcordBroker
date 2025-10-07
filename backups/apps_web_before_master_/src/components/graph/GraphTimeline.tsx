import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Calendar, Clock, TrendingUp, User, Home, DollarSign } from 'lucide-react';
import { format, parseISO } from 'date-fns';

interface TimelineEvent {
  id: string;
  timestamp: string;
  type: 'ownership_change' | 'sale' | 'price_change' | 'tax_update' | 'permit' | 'lien';
  title: string;
  description?: string;
  metadata?: {
    price?: number;
    previousOwner?: string;
    newOwner?: string;
    changePercent?: number;
    permitType?: string;
    [key: string]: any;
  };
}

interface GraphTimelineProps {
  parcelId: string;
  events?: TimelineEvent[];
  onEventClick?: (event: TimelineEvent) => void;
  maxEvents?: number;
}

const eventIcons = {
  ownership_change: User,
  sale: Home,
  price_change: TrendingUp,
  tax_update: DollarSign,
  permit: Calendar,
  lien: Clock
};

const eventColors = {
  ownership_change: 'bg-blue-500',
  sale: 'bg-green-500',
  price_change: 'bg-yellow-500',
  tax_update: 'bg-purple-500',
  permit: 'bg-orange-500',
  lien: 'bg-red-500'
};

export const GraphTimeline: React.FC<GraphTimelineProps> = ({
  parcelId,
  events: initialEvents,
  onEventClick,
  maxEvents = 10
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>(initialEvents || []);
  const [loading, setLoading] = useState(!initialEvents);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (!initialEvents && parcelId) {
      fetchTimelineEvents();
    }
  }, [parcelId]);

  const fetchTimelineEvents = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/graph/property/${parcelId}/timeline`);
      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error('Error fetching timeline:', error);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const displayEvents = expanded ? events : events.slice(0, maxEvents);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="flex gap-4">
              <div className="w-10 h-10 bg-gray-200 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-gray-200 rounded w-3/4" />
                <div className="h-3 bg-gray-200 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  if (events.length === 0) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <Clock className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No timeline events available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Property Timeline</h3>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gray-200" />
        
        {/* Events */}
        <div className="space-y-6">
          {displayEvents.map((event, index) => {
            const Icon = eventIcons[event.type];
            const colorClass = eventColors[event.type];
            
            return (
              <div 
                key={event.id} 
                className="relative flex gap-4 cursor-pointer hover:bg-gray-50 p-2 rounded transition-colors"
                onClick={() => onEventClick?.(event)}
              >
                {/* Event icon */}
                <div className={`relative z-10 w-10 h-10 rounded-full ${colorClass} flex items-center justify-center text-white`}>
                  <Icon className="h-5 w-5" />
                </div>
                
                {/* Event content */}
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium">{event.title}</h4>
                      {event.description && (
                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                      )}
                    </div>
                    <Badge variant="outline" className="ml-2">
                      {format(parseISO(event.timestamp), 'MMM d, yyyy')}
                    </Badge>
                  </div>
                  
                  {/* Metadata */}
                  {event.metadata && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {event.metadata.price && (
                        <Badge variant="secondary">
                          ${event.metadata.price.toLocaleString()}
                        </Badge>
                      )}
                      {event.metadata.changePercent && (
                        <Badge 
                          variant={event.metadata.changePercent > 0 ? 'default' : 'destructive'}
                        >
                          {event.metadata.changePercent > 0 ? '+' : ''}{event.metadata.changePercent.toFixed(1)}%
                        </Badge>
                      )}
                      {event.metadata.newOwner && (
                        <Badge variant="outline">
                          New: {event.metadata.newOwner}
                        </Badge>
                      )}
                      {event.metadata.permitType && (
                        <Badge variant="outline">
                          {event.metadata.permitType}
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        
        {/* Show more/less button */}
        {events.length > maxEvents && (
          <div className="mt-4 text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? 'Show Less' : `Show ${events.length - maxEvents} More`}
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
};

export default GraphTimeline;