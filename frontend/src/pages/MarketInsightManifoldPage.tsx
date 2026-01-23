import MarketManifoldScene from '../components/marketManifold/MarketManifoldScene';

// Colorbar legend component
function ColorbarLegend() {
  return (
    <div className="absolute right-6 top-1/2 transform -translate-y-1/2 flex flex-col items-center z-10">
      <div className="text-xs font-semibold text-gray-900 mb-2">Preference Value</div>
      <div className="relative w-8 h-64 rounded border border-gray-400 shadow-lg overflow-hidden bg-white">
        <div 
          className="absolute inset-0"
          style={{
            background: 'linear-gradient(to top, rgb(102, 51, 153) 0%, rgb(51, 128, 153) 25%, rgb(0, 179, 102) 50%, rgb(128, 204, 51) 75%, rgb(255, 230, 51) 100%)'
          }}
        />
      </div>
      <div className="flex flex-col justify-between h-64 mt-1 text-xs text-gray-900 font-medium">
        <span>10.0</span>
        <span>8.0</span>
        <span>6.0</span>
        <span>4.0</span>
        <span>2.0</span>
        <span>0</span>
      </div>
    </div>
  );
}

export default function MarketInsightManifoldPage() {
  return (
    <div className="flex flex-col h-full w-full" style={{ background: '#ffffff' }}>
      <div className="p-4 border-b border-gray-300" style={{ background: '#ffffff' }}>
        <h1 className="text-2xl font-bold text-gray-900">Market Preference Manifold</h1>
        <p className="text-sm text-gray-600 mt-1">
          Interactive 3D visualization of market preferences and dynamics
        </p>
      </div>
      <div className="flex-1 relative" style={{ minHeight: 0, background: '#ffffff' }}>
        <MarketManifoldScene />
        <ColorbarLegend />
      </div>
    </div>
  );
}
