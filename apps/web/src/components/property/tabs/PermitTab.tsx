import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  FileText, Calendar, DollarSign, User, Building, 
  CheckCircle, Clock, AlertCircle, Wrench, Home,
  HardHat, Ruler, Shield, Zap, Droplets, Wind,
  Hash, MapPin, Briefcase, TrendingUp, XCircle,
  CreditCard, Receipt, Activity, Award, Phone,
  Mail, AlertTriangle, Info, Eye
} from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface PermitTabProps {
  propertyData: any;
}

export const PermitTab: React.FC<PermitTabProps> = ({ propertyData }) => {
  const [permits, setPermits] = useState<any[]>([]);
  const [subPermits, setSubPermits] = useState<any[]>([]);
  const [inspections, setInspections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const { bcpaData } = propertyData || {};

  useEffect(() => {
    const fetchPermitData = async () => {
      if (!bcpaData?.parcel_id) {
        setLoading(false);
        return;
      }

      try {
        // First try Florida permits (statewide system)
        let permitData = [];
        
        const { data: floridaPermits, error: floridaError } = await supabase
          .from('florida_permits')
          .select('*')
          .or(`parcel_id.eq.${bcpaData.parcel_id},property_address.ilike.%${bcpaData.property_address_street}%`)
          .order('issue_date', { ascending: false });

        if (!floridaError && floridaPermits && floridaPermits.length > 0) {
          permitData = floridaPermits;
        } else {
          // Fallback to Broward permits if no Florida permits found
          const { data: browardPermits, error: browardError } = await supabase
            .from('broward_permits')
            .select('*')
            .or(`parcel_id.eq.${bcpaData.parcel_id},property_address.ilike.%${bcpaData.property_address_street}%`)
            .order('issue_date', { ascending: false });
            
          if (!browardError && browardPermits && browardPermits.length > 0) {
            permitData = browardPermits;
          }
        }

        if (permitData && permitData.length > 0) {
          // Convert Florida permit data to display format
          const convertedPermits = permitData.map(permit => convertFloridaPermitToDisplayFormat(permit));
          setPermits(convertedPermits);

          // Try to fetch sub-permits for Florida permits (if they exist)
          const permitIds = permitData.map(p => p.id);
          const { data: subPermitData } = await supabase
            .from('permit_sub_permits')
            .select('*')
            .in('parent_permit_id', permitIds);
          
          setSubPermits(subPermitData || []);

          // Try to fetch inspections for Florida permits (if they exist)
          const { data: inspectionData } = await supabase
            .from('permit_inspections')
            .select('*')
            .in('permit_id', permitIds)
            .order('inspection_date', { ascending: false });
          
          setInspections(inspectionData || []);
        } else {
          // No permits found in database - show demo data for UI demonstration
          console.log('No permits found in database - showing demo data for UI demonstration');
          const demoPermits = generateDemoPermitData(bcpaData);
          setPermits(demoPermits);
          
          // Generate demo sub-permits and inspections
          const demoSubPermits = generateDemoSubPermits();
          const demoInspections = generateDemoInspections();
          setSubPermits(demoSubPermits);
          setInspections(demoInspections);
        }
      } catch (error) {
        console.error('Error fetching permit data:', error);
        // Show empty state on error
        setPermits([]);
        setSubPermits([]);
        setInspections([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPermitData();
  }, [bcpaData]);

  const convertFloridaPermitToDisplayFormat = (floridaPermit: any) => {
    // Convert Florida permit data to match the display format
    return {
      id: floridaPermit.id,
      permit_number: floridaPermit.permit_number,
      permit_type: floridaPermit.permit_type,
      description: floridaPermit.description,
      status: floridaPermit.status,
      applicant_name: floridaPermit.applicant_name,
      contractor_name: floridaPermit.contractor_name,
      contractor_license: floridaPermit.contractor_license,
      property_address: floridaPermit.property_address,
      parcel_id: floridaPermit.parcel_id,
      folio_number: floridaPermit.folio_number,
      issue_date: floridaPermit.issue_date,
      permit_date: floridaPermit.issue_date, // Map issue_date to permit_date
      application_date: floridaPermit.issue_date, // Use same date if application_date not available
      expiration_date: floridaPermit.expiration_date,
      final_date: floridaPermit.final_date,
      co_cc_date: floridaPermit.final_date,
      job_value: floridaPermit.valuation,
      valuation: floridaPermit.valuation,
      permit_fee: floridaPermit.permit_fee,
      total_fees: floridaPermit.permit_fee,
      recorded_payments: floridaPermit.permit_fee, // Assume paid if in system
      balance: 0, // Assume no balance if in system
      source_system: floridaPermit.source_system,
      source_url: floridaPermit.source_url,
      county_name: floridaPermit.county_name,
      municipality: floridaPermit.municipality,
      jurisdiction_type: floridaPermit.jurisdiction_type,
      scraped_at: floridaPermit.scraped_at,
      raw_data: floridaPermit.raw_data,
      // Set display fields
      job_name: floridaPermit.description || floridaPermit.permit_type,
      application_type: floridaPermit.permit_type,
      inspection_status: floridaPermit.status === 'Completed' ? 'Final Approved' : 'In Progress'
    };
  };

  const generateDemoPermitData = (bcpaData: any) => {
    const permits = [];
    const currentYear = new Date().getFullYear();
    
    // Demo Building Permit
    permits.push({
      id: 1,
      permit_number: `DEMO-${currentYear}-BP-001`,
      permit_type: 'Building',
      application_type: 'Building Alteration',
      job_name: 'Kitchen and Bath Renovation (Demo)',
      description: 'This is demonstration data. Real permit data will appear when available from Hollywood Accela, Broward BCS, or ENVIROS systems.',
      status: 'Completed',
      county_name: 'Broward',
      municipality: bcpaData?.property_address_city || 'Hollywood',
      jurisdiction_type: 'city',
      source_system: 'demo_data',
      
      property_address: bcpaData?.property_address_street || 'Demo Property Address',
      parcel_id: bcpaData?.parcel_id || 'DEMO-PARCEL',
      folio_number: bcpaData?.folio_number || 'DEMO-FOLIO',
      
      application_date: `${currentYear-1}-01-05`,
      permit_date: `${currentYear-1}-01-15`,
      issue_date: `${currentYear-1}-01-15`,
      expiration_date: `${currentYear}-01-15`,
      final_date: `${currentYear-1}-06-20`,
      co_cc_date: `${currentYear-1}-06-20`,
      
      job_value: 75000,
      valuation: 75000,
      square_footage: parseInt(bcpaData?.living_area) || 2000,
      total_fees: 2500,
      permit_fee: 2500,
      recorded_payments: 2500,
      balance: 0,
      
      applicant_name: bcpaData?.owner_name || 'Demo Owner',
      applicant_address: bcpaData?.owner_address || 'Demo Address',
      applicant_phone: '(954) 555-DEMO',
      
      contractor_name: 'Demo Contractor LLC',
      contractor_address: '123 Demo Street, Fort Lauderdale, FL',
      contractor_license: 'CGC-DEMO-123',
      contractor_type: 'General Contractor',
      contractor_phone: '(954) 555-CONT',
      contractor_total_permits: 100,
      contractor_active_permits: 5,
      contractor_passed_inspections: 95,
      contractor_failed_inspections: 5,
      contractor_pass_rate: 95,
      
      inspection_status: 'Final Approved',
      source_url: '#',
      scraped_at: new Date().toISOString()
    });
    
    // Demo HVAC Permit
    permits.push({
      id: 2,
      permit_number: `DEMO-${currentYear}-HVAC-002`,
      permit_type: 'Mechanical',
      application_type: 'HVAC',
      job_name: 'AC System Replacement (Demo)',
      description: 'Demo permit showing HVAC replacement',
      status: 'Active',
      county_name: 'Broward',
      municipality: bcpaData?.property_address_city || 'Hollywood',
      
      property_address: bcpaData?.property_address_street || 'Demo Property Address',
      parcel_id: bcpaData?.parcel_id || 'DEMO-PARCEL',
      
      application_date: `${currentYear}-10-01`,
      permit_date: `${currentYear}-10-05`,
      issue_date: `${currentYear}-10-05`,
      expiration_date: `${currentYear+1}-10-05`,
      
      job_value: 8500,
      valuation: 8500,
      total_fees: 350,
      permit_fee: 350,
      recorded_payments: 350,
      balance: 0,
      
      applicant_name: bcpaData?.owner_name || 'Demo Owner',
      contractor_name: 'Demo HVAC Services',
      contractor_license: 'CAC-DEMO-456',
      contractor_type: 'HVAC Contractor',
      
      inspection_status: 'In Progress',
      source_system: 'demo_data'
    });
    
    return permits;
  };
  
  const generateDemoSubPermits = () => [
    { id: 1, parent_permit_id: 1, sub_permit_number: 'DEMO-EL-001', sub_permit_type: 'Electrical', status: 'Completed', permit_date: '2023-01-16', fees: 300 },
    { id: 2, parent_permit_id: 1, sub_permit_number: 'DEMO-PL-001', sub_permit_type: 'Plumbing', status: 'Completed', permit_date: '2023-01-18', fees: 250 }
  ];
  
  const generateDemoInspections = () => [
    { id: 1, permit_id: 1, inspection_type: 'Foundation', inspection_date: '2023-01-20', inspection_status: 'Passed', inspector_name: 'Demo Inspector' },
    { id: 2, permit_id: 1, inspection_type: 'Final', inspection_date: '2023-06-18', inspection_status: 'Passed', inspector_name: 'Demo Inspector' },
    { id: 3, permit_id: 2, inspection_type: 'Rough', inspection_date: '2024-10-10', inspection_status: 'Scheduled', inspector_name: 'Demo Inspector' }
  ];

  const generateComprehensivePermitData = (bcpaData: any) => {
    const permits = [];
    
    // Comprehensive Building Permit with ALL fields populated
    permits.push({
      id: 1,
      permit_number: `BRO-2024-BP-${Math.floor(Math.random() * 90000 + 10000)}`,
      master_permit: `2024-MP-${Math.floor(Math.random() * 9000 + 1000)}`,
      
      // Core Permit Information
      permit_type: 'Building',
      application_type: 'Building Alteration',
      job_name: 'Complete Kitchen and Master Bath Renovation',
      description: 'Full kitchen remodel with new cabinets, granite countertops, stainless steel appliances, under-cabinet lighting. Master bathroom renovation including tile shower, vanity replacement, and plumbing fixtures upgrade.',
      status: 'Completed',
      county_name: 'Broward',
      municipality: 'Hollywood',
      jurisdiction_type: 'city',
      source_system: 'hollywood_accela',
      
      // Property Information  
      property_address: bcpaData.property_address_street ? `${bcpaData.property_address_street}, ${bcpaData.property_address_city}` : '123 Main Street, Hollywood, FL 33019',
      parcel_id: bcpaData.parcel_id || '5142-29-03-4170',
      folio_number: bcpaData.folio_number || '514229034170',
      
      // Timeline & Dates
      application_date: '2024-01-05',
      permit_date: '2024-01-15',
      issue_date: '2024-01-15',
      expiration_date: '2025-01-15',
      final_date: '2024-06-20',
      co_cc_date: '2024-06-20',
      
      // Financial Information
      job_value: 85000,
      valuation: 85000,
      square_footage: 850,
      total_fees: 2850,
      permit_fee: 2850,
      recorded_payments: 2850,
      balance: 0,
      
      // Applicant Information
      applicant_name: bcpaData.owner_name || 'John & Sarah Smith',
      applicant_address: bcpaData.owner_address || `${bcpaData.property_address_street}, ${bcpaData.property_address_city}`,
      applicant_phone: '(954) 555-0100',
      applicant_email: 'johnsmith@email.com',
      
      // Contractor Information
      contractor_name: 'Premier Home Renovations LLC',
      contractor_address: '1234 Construction Blvd, Fort Lauderdale, FL 33301',
      contractor_license: 'CGC1234567',
      contractor_type: 'General Contractor',
      contractor_phone: '(954) 555-0200',
      contractor_email: 'info@premierhome.com',
      
      // Contractor Performance Metrics
      contractor_total_permits: 247,
      contractor_active_permits: 18,
      contractor_passed_inspections: 231,
      contractor_failed_inspections: 16,
      contractor_pass_rate: 94,
      
      // Inspection Status
      inspection_status: 'Final Approved',
      
      // Additional Data Points
      film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
      work_categories: ['Kitchen Remodel', 'Bathroom Renovation'],
      gis_coordinates: { lat: 26.0112, lng: -80.1496 },
      source_url: 'https://aca.hollywoodfl.org/CitizenAccess',
      scraped_at: '2024-01-16T10:30:00Z',
      
      // Raw system data
      raw_data: {
        original_permit_id: 'HLW-2024-000567',
        system_status: 'CO_ISSUED',
        last_inspection: 'FINAL',
        department: 'Building Services'
      }
    });

    // Comprehensive HVAC Permit
    permits.push({
      id: 2,
      permit_number: `BRO-2024-HVAC-${Math.floor(Math.random() * 90000 + 10000)}`,
      
      // Core Information
      permit_type: 'Mechanical',
      application_type: 'Mechanical',
      job_name: 'HVAC System Complete Replacement',
      description: '5-ton split system AC replacement with new air handler, ductwork modifications, and thermostat upgrade. Energy efficiency improvements.',
      status: 'Completed',
      county_name: 'Broward',
      municipality: 'Hollywood',
      jurisdiction_type: 'city',
      source_system: 'hollywood_accela',
      
      // Property Information
      property_address: bcpaData.property_address_street ? `${bcpaData.property_address_street}, ${bcpaData.property_address_city}` : '123 Main Street, Hollywood, FL 33019',
      parcel_id: bcpaData.parcel_id || '5142-29-03-4170',
      folio_number: bcpaData.folio_number || '514229034170',
      
      // Timeline
      application_date: '2024-01-08',
      permit_date: '2024-01-10',
      issue_date: '2024-01-10',
      expiration_date: '2024-07-10',
      final_date: '2024-01-25',
      co_cc_date: '2024-01-25',
      
      // Financial
      job_value: 12500,
      valuation: 12500,
      square_footage: parseInt(bcpaData.living_area) || 2100,
      total_fees: 450,
      permit_fee: 450,
      recorded_payments: 450,
      balance: 0,
      
      // Applicant
      applicant_name: bcpaData.owner_name || 'John & Sarah Smith',
      applicant_address: bcpaData.owner_address || `${bcpaData.property_address_street}, ${bcpaData.property_address_city}`,
      applicant_phone: '(954) 555-0100',
      
      // Contractor
      contractor_name: 'Cool Air Systems Inc',
      contractor_address: '5678 AC Drive, Pompano Beach, FL 33060',
      contractor_license: 'CAC1234567',
      contractor_type: 'Air Conditioning Contractor',
      contractor_phone: '(954) 555-0300',
      contractor_total_permits: 298,
      contractor_active_permits: 23,
      contractor_passed_inspections: 275,
      contractor_failed_inspections: 23,
      contractor_pass_rate: 92,
      
      inspection_status: 'Final Approved',
      film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
      work_categories: ['HVAC Replacement', 'Energy Efficiency'],
      source_url: 'https://aca.hollywoodfl.org/CitizenAccess',
      scraped_at: '2024-01-11T09:15:00Z'
    });

    // Active Pool Permit (if larger lot)
    if (!bcpaData.lot_size_sqft || parseInt(bcpaData.lot_size_sqft) > 8000) {
      permits.push({
        id: 3,
        permit_number: `MIA-2024-POOL-${Math.floor(Math.random() * 90000 + 10000)}`,
        master_permit: `2024-MP-${Math.floor(Math.random() * 9000 + 1000)}`,
        
        // Core Information
        permit_type: 'Pool/Spa',
        application_type: 'Pool/Spa Construction',
        job_name: 'In-ground Pool and Spa Installation',
        description: 'New 15x30 in-ground heated pool with attached spa, decorative coping, pool deck expansion, equipment installation, and landscape integration.',
        status: 'Active',
        county_name: 'Miami-Dade',
        municipality: 'Miami',
        jurisdiction_type: 'city',
        source_system: 'miami_dade_building',
        
        // Property Information
        property_address: '456 Ocean Drive, Miami, FL 33139',
        parcel_id: '0132-35-01-0010',
        folio_number: '01323501010',
        
        // Timeline
        application_date: '2024-10-15',
        permit_date: '2024-10-25',
        issue_date: '2024-10-25',
        expiration_date: '2025-10-25',
        final_date: null,
        co_cc_date: null,
        
        // Financial
        job_value: 65000,
        valuation: 65000,
        square_footage: 750,
        total_fees: 1850,
        permit_fee: 1850,
        recorded_payments: 1850,
        balance: 0,
        
        // Applicant
        applicant_name: 'Robert & Lisa Johnson',
        applicant_address: '456 Ocean Drive, Miami, FL 33139',
        applicant_phone: '(305) 555-0400',
        
        // Contractor
        contractor_name: 'Aqua Dreams Pools LLC',
        contractor_address: '3456 Pool Plaza, Plantation, FL 33324',
        contractor_license: 'CPC1234567',
        contractor_type: 'Swimming Pool Contractor',
        contractor_phone: '(954) 555-0500',
        contractor_total_permits: 89,
        contractor_active_permits: 8,
        contractor_passed_inspections: 81,
        contractor_failed_inspections: 8,
        contractor_pass_rate: 91,
        
        inspection_status: 'In Progress - Steel Inspection Pending',
        film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
        work_categories: ['Pool Construction', 'Outdoor Living'],
        source_url: 'https://www.miamidade.gov/permits',
        scraped_at: '2024-10-26T14:20:00Z'
      });
    }

    // Electrical Sub-permit
    permits.push({
      id: 4,
      permit_number: `BRO-2024-EL-${Math.floor(Math.random() * 90000 + 10000)}`,
      
      permit_type: 'Electrical',
      application_type: 'Electrical Service Upgrade',
      job_name: 'Electrical Panel Upgrade to 200 Amp',
      description: 'Upgrade main electrical service panel from 150 amp to 200 amp to support home renovation electrical load requirements.',
      status: 'Active',
      county_name: 'Broward',
      municipality: 'Hollywood',
      jurisdiction_type: 'city',
      source_system: 'hollywood_accela',
      
      property_address: bcpaData.property_address_street ? `${bcpaData.property_address_street}, ${bcpaData.property_address_city}` : '123 Main Street, Hollywood, FL 33019',
      parcel_id: bcpaData.parcel_id || '5142-29-03-4170',
      
      application_date: '2024-11-01',
      permit_date: '2024-11-05',
      issue_date: '2024-11-05',
      expiration_date: '2025-05-05',
      
      job_value: 3500,
      valuation: 3500,
      total_fees: 280,
      permit_fee: 280,
      recorded_payments: 280,
      balance: 0,
      
      applicant_name: bcpaData.owner_name || 'John & Sarah Smith',
      contractor_name: 'Reliable Electric LLC',
      contractor_license: 'EC13007890',
      contractor_type: 'Electrical Contractor',
      contractor_phone: '(954) 555-0600',
      contractor_total_permits: 156,
      contractor_active_permits: 12,
      contractor_passed_inspections: 148,
      contractor_failed_inspections: 8,
      contractor_pass_rate: 95,
      
      inspection_status: 'Rough Inspection Pending',
      source_url: 'https://aca.hollywoodfl.org/CitizenAccess',
      scraped_at: '2024-11-06T08:45:00Z'
    });

    return permits;
  };

  const generateSamplePermits = (bcpaData: any) => {
    const permits = [];
    
    // Recent renovation permit
    if (bcpaData.year_built && parseInt(bcpaData.year_built) < 2015) {
      permits.push({
        id: 1,
        permit_number: `2024-BP-${Math.floor(Math.random() * 90000 + 10000)}`,
        master_permit: `2024-MP-${Math.floor(Math.random() * 9000 + 1000)}`,
        job_value: 85000,
        square_footage: 2500,
        application_type: 'Building Alteration',
        job_name: 'Kitchen and Master Bath Renovation',
        film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
        application_date: '2024-01-05',
        permit_date: '2024-01-15',
        co_cc_date: '2024-06-20',
        total_fees: 2850,
        recorded_payments: 2850,
        balance: 0,
        status: 'Completed',
        permit_type: 'Building',
        description: 'Complete kitchen renovation including new cabinets, countertops, appliances. Master bathroom remodel with new fixtures.',
        applicant_name: bcpaData.owner_name || 'Property Owner',
        applicant_address: bcpaData.owner_address || `${bcpaData.property_address_street}, ${bcpaData.property_address_city}`,
        applicant_phone: '(954) 555-0100',
        contractor_name: 'Premier Renovations LLC',
        contractor_address: '1234 Construction Blvd, Fort Lauderdale, FL 33301',
        contractor_license: 'CGC1234567',
        contractor_type: 'General Contractor',
        contractor_phone: '(954) 555-0200',
        contractor_total_permits: 156,
        contractor_active_permits: 12,
        contractor_passed_inspections: 148,
        contractor_failed_inspections: 8,
        contractor_pass_rate: 95,
        inspection_status: 'Final Approved'
      });
    }

    // HVAC permit
    permits.push({
      id: 2,
      permit_number: `2024-HVAC-${Math.floor(Math.random() * 90000 + 10000)}`,
      job_value: 12500,
      square_footage: parseInt(bcpaData.living_area) || 2000,
      application_type: 'Mechanical',
      job_name: 'HVAC System Replacement',
      film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
      application_date: '2024-01-08',
      permit_date: '2024-01-10',
      co_cc_date: '2024-01-25',
      total_fees: 450,
      recorded_payments: 450,
      balance: 0,
      status: 'Completed',
      permit_type: 'Mechanical',
      description: '5-ton split system AC replacement with new air handler',
      applicant_name: bcpaData.owner_name || 'Property Owner',
      applicant_address: bcpaData.owner_address || `${bcpaData.property_address_street}, ${bcpaData.property_address_city}`,
      contractor_name: 'Cool Air Systems Inc',
      contractor_address: '5678 AC Drive, Pompano Beach, FL 33060',
      contractor_license: 'CAC1234567',
      contractor_type: 'Mechanical Contractor',
      contractor_phone: '(954) 555-0300',
      contractor_total_permits: 298,
      contractor_active_permits: 23,
      contractor_passed_inspections: 275,
      contractor_failed_inspections: 23,
      contractor_pass_rate: 92,
      inspection_status: 'Final Approved'
    });

    // Active pool permit for larger lots
    if (parseInt(bcpaData.lot_size_sqft) > 8000) {
      permits.push({
        id: 3,
        permit_number: `2024-POOL-${Math.floor(Math.random() * 90000 + 10000)}`,
        master_permit: `2024-MP-${Math.floor(Math.random() * 9000 + 1000)}`,
        job_value: 65000,
        square_footage: 600,
        application_type: 'Pool/Spa',
        job_name: 'In-ground Pool Installation',
        film_number: `F-2024-${Math.floor(Math.random() * 9000 + 1000)}`,
        application_date: '2024-10-15',
        permit_date: '2024-10-25',
        co_cc_date: null,
        total_fees: 1850,
        recorded_payments: 1850,
        balance: 0,
        status: 'Active',
        permit_type: 'Pool/Spa',
        description: 'New 15x30 in-ground pool with spa and deck',
        applicant_name: bcpaData.owner_name || 'Property Owner',
        contractor_name: 'Aqua Dreams Pools LLC',
        contractor_address: '3456 Pool Plaza, Plantation, FL 33324',
        contractor_license: 'CPC1234567',
        contractor_type: 'Pool Contractor',
        contractor_total_permits: 89,
        contractor_active_permits: 8,
        contractor_passed_inspections: 81,
        contractor_failed_inspections: 8,
        contractor_pass_rate: 91,
        inspection_status: 'In Progress'
      });
    }

    return permits;
  };

  const generateSampleSubPermits = () => [
    { id: 1, parent_permit_id: 1, sub_permit_number: `2024-EL-${Math.floor(Math.random() * 9000 + 1000)}`, sub_permit_type: 'Electrical', status: 'Completed', permit_date: '2024-01-16', fees: 350 },
    { id: 2, parent_permit_id: 1, sub_permit_number: `2024-PL-${Math.floor(Math.random() * 9000 + 1000)}`, sub_permit_type: 'Plumbing', status: 'Completed', permit_date: '2024-01-18', fees: 275 },
    { id: 3, parent_permit_id: 3, sub_permit_number: `2024-EL-${Math.floor(Math.random() * 9000 + 1000)}`, sub_permit_type: 'Electrical', status: 'Active', permit_date: '2024-10-26', fees: 450 },
    { id: 4, parent_permit_id: 3, sub_permit_number: `2024-PL-${Math.floor(Math.random() * 9000 + 1000)}`, sub_permit_type: 'Plumbing', status: 'Active', permit_date: '2024-10-27', fees: 320 }
  ];

  const generateSampleInspections = () => [
    { id: 1, permit_id: 1, inspection_type: 'Foundation', inspection_date: '2024-01-20', inspection_status: 'Passed', inspector_name: 'Inspector Johnson' },
    { id: 2, permit_id: 1, inspection_type: 'Framing', inspection_date: '2024-02-15', inspection_status: 'Passed', inspector_name: 'Inspector Johnson' },
    { id: 3, permit_id: 1, inspection_type: 'Final', inspection_date: '2024-06-18', inspection_status: 'Passed', inspector_name: 'Inspector Smith' },
    { id: 4, permit_id: 2, inspection_type: 'Rough', inspection_date: '2024-01-12', inspection_status: 'Passed', inspector_name: 'Inspector Brown' },
    { id: 5, permit_id: 2, inspection_type: 'Final', inspection_date: '2024-01-24', inspection_status: 'Passed', inspector_name: 'Inspector Brown' },
    { id: 6, permit_id: 3, inspection_type: 'Layout', inspection_date: '2024-10-28', inspection_status: 'Passed', inspector_name: 'Inspector Wilson' },
    { id: 7, permit_id: 3, inspection_type: 'Steel', inspection_date: '2024-12-15', inspection_status: 'Scheduled', inspector_name: 'Inspector Wilson' }
  ];


  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'final approved':
      case 'closed':
        return 'bg-green-100 text-green-800';
      case 'active':
      case 'in progress':
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
      case 'submitted':
      case 'under review':
      case 'scheduled':
        return 'bg-yellow-100 text-yellow-800';
      case 'expired':
      case 'cancelled':
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPermitIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'building':
      case 'building alteration':
        return <Building className="h-4 w-4 text-orange-600" />;
      case 'electrical':
        return <Zap className="h-4 w-4 text-yellow-600" />;
      case 'plumbing':
        return <Droplets className="h-4 w-4 text-blue-600" />;
      case 'mechanical':
      case 'hvac':
        return <Wind className="h-4 w-4 text-green-600" />;
      case 'roofing':
        return <Home className="h-4 w-4 text-red-600" />;
      case 'pool/spa':
        return <Droplets className="h-4 w-4 text-cyan-600" />;
      default:
        return <FileText className="h-4 w-4 text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse space-y-6">
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const activePermits = permits.filter(p => 
    p.status === 'Active' || p.status === 'In Progress' || p.status === 'Open'
  );

  const totalValue = permits.reduce((sum, p) => sum + (p.job_value || 0), 0);
  const totalFees = permits.reduce((sum, p) => sum + (p.total_fees || 0), 0);
  const outstandingBalance = permits.reduce((sum, p) => sum + (p.balance || 0), 0);

  return (
    <div className="space-y-6">
      {/* Active Permits Alert */}
      {activePermits.length > 0 && (
        <Alert className="border-blue-200 bg-blue-50">
          <Info className="h-4 w-4 text-blue-600" />
          <AlertTitle className="text-blue-800">Active Permits</AlertTitle>
          <AlertDescription className="text-blue-700">
            This property has {activePermits.length} active permit{activePermits.length !== 1 ? 's' : ''} currently in progress.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HardHat className="h-5 w-5 text-orange-600" />
            Building Permits Summary
          </CardTitle>
          <CardDescription>
            Comprehensive permit history and current status for this property
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-700">{permits.length}</div>
              <div className="text-sm text-gray-600">Total Permits</div>
            </div>
            <div className="text-center p-4 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-700">{activePermits.length}</div>
              <div className="text-sm text-gray-600">Active Permits</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-700">{formatCurrency(totalValue)}</div>
              <div className="text-sm text-gray-600">Total Project Value</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">{formatCurrency(totalFees)}</div>
              <div className="text-sm text-gray-600">Total Fees</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Permit Details Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="active">Active ({activePermits.length})</TabsTrigger>
          <TabsTrigger value="history">History ({permits.length - activePermits.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 mt-6">
          {permits.map((permit, index) => (
            <PermitDetailCard 
              key={permit.id || index} 
              permit={permit} 
              subPermits={subPermits.filter(sp => sp.parent_permit_id === permit.id)}
              inspections={inspections.filter(i => i.permit_id === permit.id)}
            />
          ))}
        </TabsContent>

        <TabsContent value="active" className="space-y-4 mt-6">
          {activePermits.length > 0 ? (
            activePermits.map((permit, index) => (
              <PermitDetailCard 
                key={permit.id || index} 
                permit={permit} 
                subPermits={subPermits.filter(sp => sp.parent_permit_id === permit.id)}
                inspections={inspections.filter(i => i.permit_id === permit.id)}
              />
            ))
          ) : (
            <Card>
              <CardContent className="text-center py-12">
                <CheckCircle className="h-16 w-16 text-green-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active Permits</h3>
                <p className="text-gray-600">All permits for this property have been completed or closed.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="history" className="space-y-4 mt-6">
          {permits.filter(p => p.status !== 'Active' && p.status !== 'In Progress' && p.status !== 'Open').map((permit, index) => (
            <PermitDetailCard 
              key={permit.id || index} 
              permit={permit} 
              subPermits={subPermits.filter(sp => sp.parent_permit_id === permit.id)}
              inspections={inspections.filter(i => i.permit_id === permit.id)}
            />
          ))}
        </TabsContent>
      </Tabs>

      {permits.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Building Permits in Database</h3>
            <p className="text-gray-600">
              Permit data has not been loaded for this property yet.
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Real permit records exist in municipal systems but haven't been scraped and imported.
            </p>
            {permits.some(p => p.source_system === 'demo_data') && (
              <div className="mt-4 p-3 bg-yellow-50 rounded-lg">
                <p className="text-sm text-yellow-800 font-medium">
                  ⚠️ Demonstration Data
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  Currently showing demo permits for UI demonstration purposes.
                </p>
                <p className="text-xs text-yellow-700">
                  Real permit data will be displayed once available from Hollywood Accela, Broward BCS, or ENVIROS systems.
                </p>
              </div>
            )}
            {permits.length === 0 && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-700 font-medium">
                  ℹ️ Permit Data Sources
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  Permit data is collected from Hollywood Accela, Broward County BCS, and ENVIROS systems.
                </p>
                <p className="text-xs text-blue-600">
                  Data will appear here once permits are scraped and imported for this property.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Individual Permit Detail Card Component
const PermitDetailCard: React.FC<{ 
  permit: any; 
  subPermits: any[]; 
  inspections: any[] 
}> = ({ permit, subPermits, inspections }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
      case 'final approved':
      case 'closed':
        return 'bg-green-100 text-green-800';
      case 'active':
      case 'in progress':
      case 'open':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
      case 'submitted':
      case 'under review':
      case 'scheduled':
        return 'bg-yellow-100 text-yellow-800';
      case 'expired':
      case 'cancelled':
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPermitIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'building':
      case 'building alteration':
        return <Building className="h-5 w-5 text-orange-600" />;
      case 'electrical':
        return <Zap className="h-5 w-5 text-yellow-600" />;
      case 'plumbing':
        return <Droplets className="h-5 w-5 text-blue-600" />;
      case 'mechanical':
      case 'hvac':
        return <Wind className="h-5 w-5 text-green-600" />;
      case 'roofing':
        return <Home className="h-5 w-5 text-red-600" />;
      case 'pool/spa':
        return <Droplets className="h-5 w-5 text-cyan-600" />;
      default:
        return <FileText className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex items-center gap-3">
            {getPermitIcon(permit.permit_type)}
            <div>
              <CardTitle className="text-xl">
                {permit.job_name || permit.application_type}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-1">
                <Hash className="h-4 w-4" />
                {permit.permit_number}
                {permit.master_permit && (
                  <>
                    <span className="text-gray-400">•</span>
                    Master: {permit.master_permit}
                  </>
                )}
              </CardDescription>
            </div>
          </div>
          <Badge className={getStatusColor(permit.status)}>
            {permit.status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-6">
          {/* Site Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <MapPin className="h-4 w-4 text-gray-600" />
              Site Information
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Job Value</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatCurrency(permit.job_value || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Square Footage</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {permit.square_footage?.toLocaleString() || '-'}
                    {permit.square_footage && ' sq ft'}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Application Type</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {permit.application_type || '-'}
                  </p>
                </div>
                {permit.film_number && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">Film Number</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {permit.film_number}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Permit Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-600" />
              Permit Information
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm font-medium text-gray-500">Application Date</p>
                <p className="text-base font-medium text-gray-900 flex items-center gap-1">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  {permit.application_date ? new Date(permit.application_date).toLocaleDateString() : '-'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Permit Date</p>
                <p className="text-base font-medium text-gray-900 flex items-center gap-1">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  {permit.permit_date ? new Date(permit.permit_date).toLocaleDateString() : '-'}
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">CO/CC Date</p>
                <p className="text-base font-medium text-gray-900 flex items-center gap-1">
                  {permit.co_cc_date ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      {new Date(permit.co_cc_date).toLocaleDateString()}
                    </>
                  ) : (
                    <>
                      <Clock className="h-4 w-4 text-yellow-600" />
                      Pending
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>

          {/* Financial Information */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-gray-600" />
              Fees & Payments
            </h4>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Total Fees</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {formatCurrency(permit.total_fees || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Payments</p>
                  <p className="text-lg font-semibold text-green-700">
                    {formatCurrency(permit.recorded_payments || 0)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Balance</p>
                  <p className={`text-lg font-semibold ${(permit.balance || 0) > 0 ? 'text-red-700' : 'text-green-700'}`}>
                    {formatCurrency(permit.balance || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Applicant Information */}
          {permit.applicant_name && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <User className="h-4 w-4 text-gray-600" />
                Applicant Information
              </h4>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="space-y-2">
                  <p className="font-medium text-gray-900">{permit.applicant_name}</p>
                  {permit.applicant_address && (
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <MapPin className="h-3 w-3" />
                      {permit.applicant_address}
                    </p>
                  )}
                  {permit.applicant_phone && (
                    <p className="text-sm text-gray-600 flex items-center gap-1">
                      <Phone className="h-3 w-3" />
                      {permit.applicant_phone}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Contractor Information */}
          {permit.contractor_name && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-gray-600" />
                Contractor Information
              </h4>
              <div className="bg-orange-50 p-4 rounded-lg space-y-3">
                <div className="flex justify-between items-start">
                  <div className="space-y-2">
                    <p className="font-medium text-gray-900">{permit.contractor_name}</p>
                    {permit.contractor_address && (
                      <p className="text-sm text-gray-600 flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {permit.contractor_address}
                      </p>
                    )}
                    {permit.contractor_phone && (
                      <p className="text-sm text-gray-600 flex items-center gap-1">
                        <Phone className="h-3 w-3" />
                        {permit.contractor_phone}
                      </p>
                    )}
                    {permit.contractor_license && (
                      <p className="text-sm text-gray-600">
                        License: {permit.contractor_license}
                      </p>
                    )}
                  </div>
                  {permit.contractor_type && (
                    <Badge variant="outline" className="bg-white">
                      {permit.contractor_type}
                    </Badge>
                  )}
                </div>

                {/* Contractor Performance */}
                {permit.contractor_total_permits && (
                  <div className="border-t border-orange-200 pt-3">
                    <p className="text-sm font-medium text-gray-700 mb-2">Contractor Performance</p>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                      <div className="text-center">
                        <p className="text-lg font-bold text-blue-700">
                          {permit.contractor_total_permits}
                        </p>
                        <p className="text-xs text-gray-600">Total Permits</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-yellow-700">
                          {permit.contractor_active_permits}
                        </p>
                        <p className="text-xs text-gray-600">Active</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-green-700">
                          {permit.contractor_passed_inspections}
                        </p>
                        <p className="text-xs text-gray-600">Passed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-red-700">
                          {permit.contractor_failed_inspections}
                        </p>
                        <p className="text-xs text-gray-600">Failed</p>
                      </div>
                      <div className="text-center">
                        <p className="text-lg font-bold text-blue-700">
                          {permit.contractor_pass_rate}%
                        </p>
                        <p className="text-xs text-gray-600">Pass Rate</p>
                      </div>
                    </div>
                    <Progress 
                      value={permit.contractor_pass_rate || 0} 
                      className="h-2 mt-2 bg-orange-100"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Sub-permits */}
          {subPermits.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Hash className="h-4 w-4 text-gray-600" />
                Sub-Permits ({subPermits.length})
              </h4>
              <div className="space-y-2">
                {subPermits.map((sub, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      {getPermitIcon(sub.sub_permit_type)}
                      <span className="font-medium text-gray-900">
                        {sub.sub_permit_number}
                      </span>
                      <span className="text-gray-600">- {sub.sub_permit_type}</span>
                      {sub.fees && (
                        <span className="text-sm text-gray-500">
                          ({formatCurrency(sub.fees)})
                        </span>
                      )}
                    </div>
                    <Badge className={getStatusColor(sub.status)} variant="outline">
                      {sub.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Inspections */}
          {inspections.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Eye className="h-4 w-4 text-gray-600" />
                Inspection History ({inspections.length})
              </h4>
              <div className="space-y-2">
                {inspections.map((inspection, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-500" />
                      <span className="font-medium text-gray-900">
                        {inspection.inspection_type}
                      </span>
                      <span className="text-gray-600">
                        - {new Date(inspection.inspection_date).toLocaleDateString()}
                      </span>
                      {inspection.inspector_name && (
                        <span className="text-sm text-gray-500">
                          by {inspection.inspector_name}
                        </span>
                      )}
                    </div>
                    <Badge className={getStatusColor(inspection.inspection_status)} variant="outline">
                      {inspection.inspection_status === 'Passed' && <CheckCircle className="h-3 w-3 mr-1" />}
                      {inspection.inspection_status === 'Failed' && <XCircle className="h-3 w-3 mr-1" />}
                      {inspection.inspection_status === 'Scheduled' && <Clock className="h-3 w-3 mr-1" />}
                      {inspection.inspection_status}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Description */}
          {permit.description && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Description</h4>
              <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                {permit.description}
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
