import React from 'react'
import EnhancedPropertyProfile from '../property/EnhancedPropertyProfile'

interface PropertyPageProps {}

export default function PropertyKerasPage({}: PropertyPageProps) {
  // This component now just wraps the EnhancedPropertyProfile
  // which has all the tabs and proper design
  return <EnhancedPropertyProfile />
}