import React from 'react';
import NotificationBell from './NotificationBell';

// Example usage of the enhanced NotificationBell component
// You can integrate this into your header, navbar, or dashboard

export const NotificationBellExample = () => {
  const handleNotificationClick = () => {
    console.log('Notification bell clicked!');
    // Add your notification panel open logic here
  };

  return (
    <div className="flex items-center justify-end p-4">
      {/* Enhanced 3D Animated Notification Bell */}
      <NotificationBell 
        count={3} 
        onClick={handleNotificationClick}
      />
    </div>
  );
};

// To use in your existing layout/header, replace the old bell with:
// <NotificationBell count={notificationCount} onClick={openNotificationPanel} />

export default NotificationBellExample;