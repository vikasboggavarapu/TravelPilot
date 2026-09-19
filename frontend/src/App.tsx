import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import PlanTrip from './pages/PlanTrip';
import TripView from './pages/TripView';
import './index.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/plan" element={<PlanTrip />} />
        <Route path="/trip/:tripId" element={<TripView />} />
      </Routes>
    </BrowserRouter>
  );
}
