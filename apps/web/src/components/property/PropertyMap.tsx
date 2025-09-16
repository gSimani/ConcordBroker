import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { MapPin, Navigation, ZoomIn, ZoomOut, Layers, X } from 'lucide-react';
import '@/styles/elegant-property.css';

declare global {
  interface Window {
    google: any;
    initMap: () => void;
  }
}

interface Property {
  id: number;
  parcel_id: string;
  phy_addr1: string;
  phy_city: string;
  phy_zipcd: string;
  own_name: string;
  property_type: string;
  jv: number;
  tv_sd: number;
  lnd_val: number;
  tot_lvg_area: number;
  lnd_sqfoot: number;
  act_yr_blt: number;
  sale_prc1?: number;
  sale_yr1?: number;
}

interface PropertyMapProps {
  properties: Property[];
  onPropertySelect: (property: Property) => void;
  onClose: () => void;
  selectedProperty?: Property | null;
  showingSelectedOnly?: boolean;
  totalSelected?: number;
}

export function PropertyMap({ properties, onPropertySelect, onClose, selectedProperty, showingSelectedOnly = false, totalSelected = 0 }: PropertyMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const infoWindowRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const geocoderRef = useRef<any>(null);
  const GOOGLE_MAPS_KEY = (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY;

  // Initialize Google Maps
  useEffect(() => {
    const loadGoogleMaps = () => {
      if (window.google && window.google.maps) {
        initializeMap();
        return;
      }

      // Check if script is already loading
      if (document.querySelector('script[src*="maps.googleapis.com"]')) {
        const checkGoogle = setInterval(() => {
          if (window.google && window.google.maps) {
            clearInterval(checkGoogle);
            initializeMap();
          }
        }, 100);
        return;
      }

      // For demo purposes, simulate map loading
      setTimeout(() => {
        setIsLoading(false);
        setMapReady(true);
        setError(null);
      }, 1000);
    };

    const initializeMap = () => {
      if (!mapRef.current || !window.google) return;

      try {
        // Initialize map centered on Broward County
        const map = new window.google.maps.Map(mapRef.current, {
          zoom: 10,
          center: { lat: 26.1224, lng: -80.1373 }, // Fort Lauderdale center
          mapTypeId: 'roadmap',
          styles: [
            {
              featureType: 'water',
              elementType: 'geometry',
              stylers: [{ color: '#e9e9e9' }, { lightness: 17 }]
            },
            {
              featureType: 'landscape',
              elementType: 'geometry',
              stylers: [{ color: '#f5f5f5' }, { lightness: 20 }]
            },
            {
              featureType: 'road.highway',
              elementType: 'geometry.fill',
              stylers: [{ color: '#ffffff' }, { lightness: 17 }]
            },
            {
              featureType: 'road.highway',
              elementType: 'geometry.stroke',
              stylers: [{ color: '#ffffff' }, { lightness: 29 }, { weight: 0.2 }]
            },
            {
              featureType: 'road.arterial',
              elementType: 'geometry',
              stylers: [{ color: '#ffffff' }, { lightness: 18 }]
            },
            {
              featureType: 'road.local',
              elementType: 'geometry',
              stylers: [{ color: '#ffffff' }, { lightness: 16 }]
            },
            {
              featureType: 'poi',
              elementType: 'geometry',
              stylers: [{ color: '#f5f5f5' }, { lightness: 21 }]
            }
          ]
        });

        mapInstanceRef.current = map;
        geocoderRef.current = new window.google.maps.Geocoder();
        infoWindowRef.current = new window.google.maps.InfoWindow();
        
        setMapReady(true);
        setIsLoading(false);
        setError(null);
        
      } catch (err) {
        console.error('Error initializing map:', err);
        setError('Failed to initialize map');
        setIsLoading(false);
      }
    };

    loadGoogleMaps();
  }, []);

  // Add property markers to map
  useEffect(() => {
    if (!mapReady || !properties.length || !mapInstanceRef.current) return;

    // Clear existing markers
    markersRef.current.forEach(marker => marker.setMap(null));
    markersRef.current = [];

    // Add markers for each property
    const bounds = new window.google.maps.LatLngBounds();
    let processed = 0;
    
    properties.forEach(property => {
      const address = `${property.phy_addr1}, ${property.phy_city}, FL ${property.phy_zipcd}`;
      
      // Geocode the address
      geocoderRef.current.geocode({ address }, (results: any, status: any) => {
        processed++;
        
        if (status === 'OK' && results[0]) {
          const position = results[0].geometry.location;
          
          // Create marker
          const marker = new window.google.maps.Marker({
            position,
            map: mapInstanceRef.current,
            title: property.phy_addr1,
            icon: {
              url: `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`
                <svg width="30" height="40" viewBox="0 0 30 40" xmlns="http://www.w3.org/2000/svg">
                  <path d="M15 0C6.716 0 0 6.716 0 15c0 8.284 15 25 15 25s15-16.716 15-25C30 6.716 23.284 0 15 0z" fill="#d4af37"/>
                  <circle cx="15" cy="15" r="8" fill="#2c3e50"/>
                  <text x="15" y="19" text-anchor="middle" fill="white" font-size="10" font-weight="bold">$</text>
                </svg>
              `)}`,
              scaledSize: new window.google.maps.Size(30, 40),
              anchor: new window.google.maps.Point(15, 40)
            }
          });

          // Create info window content
          const infoContent = `
            <div class="p-4 max-w-sm" style="font-family: system-ui, -apple-system, sans-serif;">
              <div class="mb-3">
                <h3 class="text-lg font-semibold" style="color: #2c3e50; margin: 0 0 8px 0;">
                  ${property.phy_addr1}
                </h3>
                <p class="text-sm" style="color: #7f8c8d; margin: 0;">
                  ${property.phy_city}, FL ${property.phy_zipcd}
                </p>
              </div>
              <div class="grid grid-cols-2 gap-3 mb-3 text-sm">
                <div>
                  <span style="color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Just Value</span>
                  <div style="color: #2c3e50; font-weight: 600;">$${property.jv?.toLocaleString() || 'N/A'}</div>
                </div>
                <div>
                  <span style="color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Property Type</span>
                  <div style="color: #2c3e50; font-weight: 600;">${property.property_type}</div>
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3 mb-4 text-sm">
                <div>
                  <span style="color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Living Area</span>
                  <div style="color: #2c3e50; font-weight: 600;">${property.tot_lvg_area?.toLocaleString() || 'N/A'} sq ft</div>
                </div>
                <div>
                  <span style="color: #95a5a6; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Built Year</span>
                  <div style="color: #2c3e50; font-weight: 600;">${property.act_yr_blt || 'N/A'}</div>
                </div>
              </div>
              <button onclick="window.selectProperty(${property.id})" 
                style="background: #d4af37; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-size: 14px; cursor: pointer; width: 100%;">
                View Details
              </button>
            </div>
          `;

          // Add click listener
          marker.addListener('click', () => {
            infoWindowRef.current.setContent(infoContent);
            infoWindowRef.current.open(mapInstanceRef.current, marker);
            
            // Store reference for property selection
            window.selectProperty = (id: number) => {
              const selectedProp = properties.find(p => p.id === id);
              if (selectedProp) {
                onPropertySelect(selectedProp);
              }
            };
          });

          markersRef.current.push(marker);
          bounds.extend(position);
        }
        
        // Fit bounds when all markers are processed
        if (processed === properties.length && markersRef.current.length > 0) {
          if (markersRef.current.length === 1) {
            mapInstanceRef.current.setCenter(bounds.getCenter());
            mapInstanceRef.current.setZoom(16);
          } else {
            mapInstanceRef.current.fitBounds(bounds);
          }
        }
      });
    });
    
  }, [mapReady, properties, onPropertySelect]);

  // Highlight selected property
  useEffect(() => {
    if (!selectedProperty || !markersRef.current.length) return;

    markersRef.current.forEach((marker, index) => {
      const property = properties[index];
      if (property && property.id === selectedProperty.id) {
        // Bounce animation and different icon for selected property
        marker.setAnimation(window.google.maps.Animation.BOUNCE);
        setTimeout(() => marker.setAnimation(null), 2000);
        
        // Center map on selected property
        mapInstanceRef.current.setCenter(marker.getPosition());
        mapInstanceRef.current.setZoom(17);
      }
    });
  }, [selectedProperty, properties]);

  if (error) {
    return (
      <div className="elegant-card">
        <CardHeader className="elegant-card-header">
          <div className="flex items-center justify-between">
            <CardTitle className="elegant-card-title gold-accent flex items-center">
              <MapPin className="w-5 h-5 mr-2" style={{color: '#2c3e50'}} />
              Map View
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-8 text-center">
          <div className="text-red-500 mb-4">
            <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p style={{color: '#e74c3c'}}>{error}</p>
            <p className="text-sm mt-2" style={{color: '#7f8c8d'}}>
              Map functionality requires Google Maps API integration
            </p>
          </div>
        </CardContent>
      </div>
    );
  }

  return (
    <div className="elegant-card hover-lift animate-in">
      <div className="elegant-card-header">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <MapPin className="w-5 h-5 mr-2" style={{color: '#2c3e50'}} />
            <h3 className="elegant-card-title gold-accent">
              {showingSelectedOnly ? 'Selected Property Locations' : 'Property Locations'}
            </h3>
            <Badge variant="secondary" className="ml-3" style={{background: 'rgba(212, 175, 55, 0.1)', color: '#d4af37', border: '1px solid #d4af37'}}>
              {showingSelectedOnly ? `${properties.length} Selected` : `${properties.length} Properties`}
            </Badge>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose} className="hover-lift">
            <X className="w-4 h-4" style={{color: '#2c3e50'}} />
          </Button>
        </div>
        <p className="text-sm mt-3" style={{color: '#7f8c8d'}}>
          {showingSelectedOnly 
            ? `Interactive map showing ${properties.length} selected properties with exact locations and details`
            : 'Interactive map showing exact property locations with details'
          }
        </p>
      </div>
      
      <div className="relative">
        {isLoading && (
          <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
            <div className="text-center">
              <div className="animate-spin w-8 h-8 border-2 border-gold border-t-transparent rounded-full mx-auto mb-4"></div>
              <p style={{color: '#7f8c8d'}}>Loading map...</p>
            </div>
          </div>
        )}
        
        <div 
          ref={mapRef} 
          className="w-full rounded-lg relative overflow-hidden"
          style={{minHeight: '600px', background: '#f0f0f0'}}
        >
          {/* Embedded Google Maps using iframe */}
          {properties.length > 0 ? (
            <>
              {/* Create a Google Maps embed URL with multiple markers */}
              <iframe
                width="100%"
                height="600"
                style={{border: 0}}
                loading="lazy"
                allowFullScreen
                referrerPolicy="no-referrer-when-downgrade"
                src={`https://www.google.com/maps/embed/v1/search?key=${GOOGLE_MAPS_KEY || ''}&q=${encodeURIComponent(
                  properties.map(p => `${p.phy_addr1} ${p.phy_city} FL ${p.phy_zipcd}`).join('|')
                )}&center=26.1224,-80.1373&zoom=11`}
              />
              
              {/* Property List Overlay */}
              <div className="absolute top-4 left-4 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-4 max-w-sm max-h-96 overflow-y-auto">
                <h4 className="font-semibold text-sm mb-3" style={{color: '#2c3e50'}}>
                  Selected Properties ({properties.length})
                </h4>
                <div className="space-y-2">
                  {properties.map((property, index) => (
                    <div 
                      key={property.id}
                      className="border-l-2 pl-3 py-2 hover:bg-gray-50 cursor-pointer"
                      style={{borderColor: '#d4af37'}}
                      onClick={() => {
                        // Open in Google Maps
                        window.open(
                          `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                            `${property.phy_addr1} ${property.phy_city} FL ${property.phy_zipcd}`
                          )}`,
                          '_blank'
                        );
                      }}
                    >
                      <div className="flex items-start space-x-2">
                        <span className="text-xs font-bold" style={{color: '#d4af37'}}>
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-xs font-medium" style={{color: '#2c3e50'}}>
                            {property.phy_addr1}
                          </p>
                          <p className="text-xs" style={{color: '#7f8c8d'}}>
                            {property.phy_city}, FL {property.phy_zipcd}
                          </p>
                          <p className="text-xs font-medium" style={{color: '#27ae60'}}>
                            ${property.jv?.toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-3 pt-3 border-t">
                  <button
                    onClick={() => {
                      // Open all in Google Maps
                      const addresses = properties.map(p => 
                        `${p.phy_addr1} ${p.phy_city} FL ${p.phy_zipcd}`
                      ).join('/');
                      window.open(
                        `https://www.google.com/maps/dir/${encodeURIComponent(addresses)}`,
                        '_blank'
                      );
                    }}
                    className="text-xs font-medium px-3 py-1 rounded"
                    style={{background: '#d4af37', color: 'white'}}
                  >
                    View Route in Google Maps
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <MapPin className="w-12 h-12 mx-auto mb-4" style={{color: '#95a5a6'}} />
                <p style={{color: '#7f8c8d'}}>No properties to display</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Map Controls */}
        <div className="absolute top-4 right-4 flex flex-col space-y-2">
          <Button 
            size="sm" 
            className="hover-lift bg-white shadow-md"
            style={{color: '#2c3e50', border: '1px solid #ecf0f1'}}
            onClick={() => mapInstanceRef.current?.setZoom(mapInstanceRef.current.getZoom() + 1)}
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button 
            size="sm" 
            className="hover-lift bg-white shadow-md"
            style={{color: '#2c3e50', border: '1px solid #ecf0f1'}}
            onClick={() => mapInstanceRef.current?.setZoom(mapInstanceRef.current.getZoom() - 1)}
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <Button 
            size="sm" 
            className="hover-lift bg-white shadow-md"
            style={{color: '#2c3e50', border: '1px solid #ecf0f1'}}
            onClick={() => {
              if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(position => {
                  const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                  };
                  mapInstanceRef.current?.setCenter(pos);
                  mapInstanceRef.current?.setZoom(15);
                });
              }
            }}
          >
            <Navigation className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
