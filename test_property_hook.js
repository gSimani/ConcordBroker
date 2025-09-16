// Test the property data loading directly
console.log('Testing property data loading...');

// Simulate the usePropertyData hook logic
const addressOrParcelId = '12681 nw 78 mnr';
const city = 'parkland';

console.log('Input:', { addressOrParcelId, city });

// Check if it's a parcel ID
const isParcelId = /^\d/.test(addressOrParcelId);
console.log('Is Parcel ID:', isParcelId);

// Normalize address
const normalizedAddress = addressOrParcelId.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
console.log('Normalized Address:', normalizedAddress);

// Test the ilike pattern
console.log('ILIKE Pattern:', `%${addressOrParcelId}%`);
console.log('OR Pattern:', `phy_addr1.ilike.%${addressOrParcelId}%,parcel_id.eq.${addressOrParcelId}`);

// Expected matches
const testAddresses = [
    '12681 NW 78 MNR',
    '12681 nw 78 mnr', 
    '12681-nw-78-mnr'
];

testAddresses.forEach(addr => {
    const matches = addr.toLowerCase().includes(normalizedAddress.toLowerCase());
    console.log(`"${addr}" matches "${normalizedAddress}":`, matches);
});