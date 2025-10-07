import React from 'react';
import { motion } from 'framer-motion';

interface NotificationBellProps {
  count?: number;
  onClick?: () => void;
}

export const NotificationBell: React.FC<NotificationBellProps> = ({ count = 0, onClick }) => {
  return (
    <motion.button
      onClick={onClick}
      className="relative p-3 rounded-full hover:bg-gradient-to-br hover:from-gray-50 hover:to-gray-100 transition-all duration-300 group"
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.95 }}
    >
      {/* 3D Bell Icon with Gradient and Shadow */}
      <motion.div
        className="relative"
        animate={{
          rotateZ: [0, -15, 15, -15, 15, 0],
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          repeatDelay: 5,
          ease: "easeInOut"
        }}
      >
        <svg
          className="w-8 h-8"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Gradient Definition */}
          <defs>
            <linearGradient id="bellGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{ stopColor: '#d4af37', stopOpacity: 1 }} />
              <stop offset="100%" style={{ stopColor: '#2c3e50', stopOpacity: 1 }} />
            </linearGradient>
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.3"/>
            </filter>
          </defs>
          
          {/* Bell Shape with 3D Effect */}
          <path
            d="M12 2C10.3431 2 9 3.34315 9 5C9 5.27906 9.02728 5.55161 9.07938 5.81479C6.66739 6.71607 5 9.13083 5 12C5 14.2375 4.5 16.5 3.5 18.5C3.22422 19.0523 3 19.5 3 20C3 20.5523 3.44772 21 4 21H20C20.5523 21 21 20.5523 21 20C21 19.5 20.7758 19.0523 20.5 18.5C19.5 16.5 19 14.2375 19 12C19 9.13083 17.3326 6.71607 14.9206 5.81479C14.9727 5.55161 15 5.27906 15 5C15 3.34315 13.6569 2 12 2Z"
            fill="url(#bellGradient)"
            stroke="url(#bellGradient)"
            strokeWidth="0.5"
            filter="url(#shadow)"
            className="group-hover:fill-current group-hover:text-amber-500 transition-colors duration-300"
          />
          
          {/* Bell Clapper */}
          <circle 
            cx="12" 
            cy="21" 
            r="1.5" 
            fill="url(#bellGradient)"
            className="group-hover:fill-current group-hover:text-amber-500 transition-colors duration-300"
          />
          
          {/* Bottom Curve */}
          <path
            d="M10.3 21C10.4673 21.5978 10.8482 22.1117 11.364 22.4428C11.8798 22.7738 12.4958 22.8993 13.0945 22.7961C13.6933 22.693 14.2339 22.368 14.6149 21.8801C14.9958 21.3922 15.191 20.7746 15.1613 20.1464"
            stroke="url(#bellGradient)"
            strokeWidth="2"
            strokeLinecap="round"
            fill="none"
            className="group-hover:stroke-amber-500 transition-colors duration-300"
          />
        </svg>
        
        {/* Animated Ring Effect */}
        <motion.div
          className="absolute inset-0 rounded-full"
          animate={{
            scale: [1, 1.5, 1.5],
            opacity: [0, 0.3, 0],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            repeatDelay: 3,
          }}
          style={{
            background: 'radial-gradient(circle, rgba(212, 175, 55, 0.3) 0%, transparent 70%)',
          }}
        />
      </motion.div>

      {/* Notification Badge */}
      {count > 0 && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-1 -right-1 min-w-[24px] h-6 flex items-center justify-center px-1.5 text-xs font-bold text-white rounded-full shadow-lg"
          style={{
            background: 'linear-gradient(135deg, #e74c3c 0%, #c0392b 100%)',
            border: '2px solid white',
            boxShadow: '0 2px 8px rgba(231, 76, 60, 0.5)',
          }}
        >
          <motion.span
            animate={{
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            {count > 99 ? '99+' : count}
          </motion.span>
        </motion.div>
      )}
    </motion.button>
  );
};

export default NotificationBell;