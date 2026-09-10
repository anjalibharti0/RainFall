import { useState } from 'react';
import { useToast } from '../context/ToastContext';
import {
  User, Globe, Bell, Map, Database, Palette, Download,
  Save, RotateCcw, ChevronRight, Check, Monitor, Moon, Sun,
  CloudRain, Thermometer, Clock, Shield, Eye, Sliders
} from 'lucide-react';

const UNITS = [
  { id: 'mm', label: 'Millimeters (mm)' },
  { id: 'cm', label: 'Centimeters (cm)' },
  { id: 'inches', label: 'Inches (in)' },
];

const TILE_LAYERS = [
  { id: 'light', label: 'Light (CARTO)', url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png' },
  { id: 'dark', label: 'Dark (CARTO)', url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png' },
  { id: 'osm', label: 'OpenStreetMap', url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png' },
  { id: 'satellite', label: 'Satellite (Esri)', url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}' },
];

const ZONE_OPTIONS = [
  { id: 'IST', label: 'IST (UTC+5:30)', offset: '+05:30' },
  { id: 'UTC', label: 'UTC (GMT)', offset: '+00:00' },
  { id: 'PST', label: 'PST (UTC-8)', offset: '-08:00' },
  { id: 'CET', label: 'CET (UTC+1)', offset: '+01:00' },
];

const LANGUAGES = [
  { id: 'en', label: 'English' },
  { id: 'hi', label: 'Hindi' },
  { id: 'bn', label: 'Bengali' },
  { id: 'ta', label: 'Tamil' },
  { id: 'te', label: 'Telugu' },
  { id: 'mr', label: 'Marathi' },
];

const DEFAULT_SETTINGS = {
  // General
  language: 'en',
  timezone: 'IST',
  dateFormat: 'DD/MM/YYYY',

  // Map
  tileLayer: 'light',
  defaultZoom: 5,
  gridOpacity: 85,
  showDistrictMarkers: true,
  showGridLines: false,

  // Data
  refreshInterval: 300,
  cacheEnabled: true,
  cacheExpiry: 3600,
  dataSource: 'imd-gfs',

  // Display
  unit: 'mm',
  decimalPrecision: 1,
  colorScheme: 'imd-standard',
  showProbabilities: true,

  // Notifications
  enableNotifications: true,
  extremeThreshold: 5,
  heavyThreshold: 50,
  soundEnabled: false,
  emailAlerts: false,

  // Export
  exportFormat: 'csv',
  includeMetadata: true,
  autoExport: false,

  // Theme
  theme: 'light',
};

function Toggle({ enabled, onChange }) {
  return (
    <button
      onClick={() => onChange(!enabled)}
      className={`relative w-10 h-[22px] rounded-full transition-colors duration-200 ${
        enabled ? 'bg-blue-600' : 'bg-gray-200'
      }`}
    >
      <span
        className={`absolute top-[2px] left-[2px] w-[18px] h-[18px] rounded-full bg-white shadow-sm transition-transform duration-200 ${
          enabled ? 'translate-x-[18px]' : ''
        }`}
      />
    </button>
  );
}

function Select({ value, onChange, options, placeholder }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full appearance-none bg-white border border-gray-200 rounded-lg px-3 py-2.5 pr-8 text-[13px] font-medium text-gray-700 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-500/10 transition-all"
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt.id} value={opt.id}>{opt.label}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
    </div>
  );
}

function Slider({ value, onChange, min = 0, max = 100, unit = '%' }) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="flex-1 h-1.5 bg-gray-200 rounded-full appearance-none cursor-pointer accent-blue-600"
      />
      <span className="text-[13px] font-semibold text-gray-700 w-12 text-right">{value}{unit}</span>
    </div>
  );
}

function Section({ icon: Icon, title, description, children }) {
  return (
    <div className="dashboard-card overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
          <Icon className="w-[18px] h-[18px] text-blue-600" />
        </div>
        <div>
          <h3 className="text-[14px] font-bold text-gray-900">{title}</h3>
          <p className="text-[11px] text-gray-400">{description}</p>
        </div>
      </div>
      <div className="p-6 space-y-5">
        {children}
      </div>
    </div>
  );
}

function Field({ label, description, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
      <div className="flex-1 min-w-0">
        <div className="text-[13px] font-semibold text-gray-700">{label}</div>
        {description && <div className="text-[11px] text-gray-400 mt-0.5">{description}</div>}
      </div>
      <div className="w-full sm:w-[240px] flex-shrink-0">
        {children}
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { toast } = useToast();
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [hasChanges, setHasChanges] = useState(false);

  const update = (key, value) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
    setHasChanges(true);
  };

  const handleSave = () => {
    setHasChanges(false);
    toast.success('Settings saved successfully');
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    setHasChanges(false);
    toast.info('Settings reset to defaults');
  };

  return (
    <div className="max-w-[900px] space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[22px] font-extrabold text-gray-900 tracking-[-0.02em]">Settings</h2>
          <p className="text-[13px] text-gray-400 mt-0.5">Configure your forecast dashboard preferences</p>
        </div>
        <div className="flex items-center gap-2">
          {hasChanges && (
            <span className="text-[11px] font-semibold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-lg">
              Unsaved changes
            </span>
          )}
          <button onClick={handleReset} className="btn-ghost">
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
          <button onClick={handleSave} className="btn-primary">
            <Save className="w-3.5 h-3.5" />
            Save Settings
          </button>
        </div>
      </div>

      {/* General */}
      <Section icon={Globe} title="General" description="Language, timezone, and regional preferences">
        <Field label="Language" description="Interface language for the dashboard">
          <Select
            value={settings.language}
            onChange={(v) => update('language', v)}
            options={LANGUAGES}
          />
        </Field>
        <Field label="Timezone" description="Used for forecast timestamps">
          <Select
            value={settings.timezone}
            onChange={(v) => update('timezone', v)}
            options={ZONE_OPTIONS}
          />
        </Field>
        <Field label="Date Format" description="How dates are displayed">
          <Select
            value={settings.dateFormat}
            onChange={(v) => update('dateFormat', v)}
            options={[
              { id: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
              { id: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
              { id: 'YYYY-MM-DD', label: 'YYYY-MM-DD' },
            ]}
          />
        </Field>
      </Section>

      {/* Map */}
      <Section icon={Map} title="Map Settings" description="Configure map display and visualization">
        <Field label="Base Map Style" description="Background tile layer for maps">
          <Select
            value={settings.tileLayer}
            onChange={(v) => update('tileLayer', v)}
            options={TILE_LAYERS}
          />
        </Field>
        <Field label="Default Zoom Level" description="Initial zoom when maps load">
          <Slider
            value={settings.defaultZoom}
            onChange={(v) => update('defaultZoom', v)}
            min={3}
            max={10}
            unit=""
          />
        </Field>
        <Field label="Grid Cell Opacity" description="Transparency of rainfall grid cells">
          <Slider
            value={settings.gridOpacity}
            onChange={(v) => update('gridOpacity', v)}
          />
        </Field>
        <Field label="Show District Markers" description="Display district location dots on the map">
          <Toggle
            enabled={settings.showDistrictMarkers}
            onChange={(v) => update('showDistrictMarkers', v)}
          />
        </Field>
        <Field label="Show Grid Lines" description="Display grid cell borders">
          <Toggle
            enabled={settings.showGridLines}
            onChange={(v) => update('showGridLines', v)}
          />
        </Field>
      </Section>

      {/* Data */}
      <Section icon={Database} title="Data & Performance" description="Data refresh, caching, and source settings">
        <Field label="Auto Refresh Interval" description="How often to check for new forecast data">
          <Select
            value={settings.refreshInterval}
            onChange={(v) => update('refreshInterval', parseInt(v))}
            options={[
              { id: 60, label: 'Every 1 minute' },
              { id: 300, label: 'Every 5 minutes' },
              { id: 600, label: 'Every 10 minutes' },
              { id: 1800, label: 'Every 30 minutes' },
              { id: 3600, label: 'Every 1 hour' },
              { id: 0, label: 'Manual only' },
            ]}
          />
        </Field>
        <Field label="Enable Cache" description="Cache forecast data to reduce API calls">
          <Toggle
            enabled={settings.cacheEnabled}
            onChange={(v) => update('cacheEnabled', v)}
          />
        </Field>
        {settings.cacheEnabled && (
          <Field label="Cache Expiry" description="How long cached data remains valid">
            <Select
              value={settings.cacheExpiry}
              onChange={(v) => update('cacheExpiry', parseInt(v))}
              options={[
                { id: 300, label: '5 minutes' },
                { id: 600, label: '10 minutes' },
                { id: 1800, label: '30 minutes' },
                { id: 3600, label: '1 hour' },
                { id: 7200, label: '2 hours' },
              ]}
            />
          </Field>
        )}
        <Field label="Data Source" description="NWP model data provider">
          <Select
            value={settings.dataSource}
            onChange={(v) => update('dataSource', v)}
            options={[
              { id: 'imd-gfs', label: 'IMD GFS (Recommended)' },
              { id: 'imd-ecmwf', label: 'IMD ECMWF' },
              { id: 'imd-ukmo', label: 'IMD UKMO' },
              { id: 'custom', label: 'Custom API Endpoint' },
            ]}
          />
        </Field>
      </Section>

      {/* Display */}
      <Section icon={Eye} title="Display Preferences" description="Units, precision, and visual settings">
        <Field label="Rainfall Unit" description="Unit for displaying rainfall amounts">
          <Select
            value={settings.unit}
            onChange={(v) => update('unit', v)}
            options={UNITS}
          />
        </Field>
        <Field label="Decimal Precision" description="Number of decimal places for values">
          <Slider
            value={settings.decimalPrecision}
            onChange={(v) => update('decimalPrecision', v)}
            min={0}
            max={3}
            unit=""
          />
        </Field>
        <Field label="Color Scheme" description="Rainfall intensity color scale">
          <Select
            value={settings.colorScheme}
            onChange={(v) => update('colorScheme', v)}
            options={[
              { id: 'imd-standard', label: 'IMD Standard' },
              { id: 'rainbow', label: 'Rainbow' },
              { id: 'heat', label: 'Heat Map' },
              { id: 'ocean', label: 'Ocean' },
            ]}
          />
        </Field>
        <Field label="Show Exceedance Probabilities" description="Display probability values in district cards">
          <Toggle
            enabled={settings.showProbabilities}
            onChange={(v) => update('showProbabilities', v)}
          />
        </Field>
      </Section>

      {/* Notifications */}
      <Section icon={Bell} title="Notifications" description="Alert thresholds and notification preferences">
        <Field label="Enable Notifications" description="Show toast alerts for weather events">
          <Toggle
            enabled={settings.enableNotifications}
            onChange={(v) => update('enableNotifications', v)}
          />
        </Field>
        {settings.enableNotifications && (
          <>
            <Field label="Extreme Rain Alert Threshold" description="Trigger alert when P(Extreme) exceeds this %">
              <Slider
                value={settings.extremeThreshold}
                onChange={(v) => update('extremeThreshold', v)}
                min={1}
                max={20}
                unit="%"
              />
            </Field>
            <Field label="Heavy Rain Alert Threshold" description="Trigger alert when P(Heavy) exceeds this %">
              <Slider
                value={settings.heavyThreshold}
                onChange={(v) => update('heavyThreshold', v)}
                min={10}
                max={90}
                unit="%"
              />
            </Field>
            <Field label="Sound Alerts" description="Play a sound when critical alerts arrive">
              <Toggle
                enabled={settings.soundEnabled}
                onChange={(v) => update('soundEnabled', v)}
              />
            </Field>
            <Field label="Email Alerts" description="Send email notifications for extreme events">
              <Toggle
                enabled={settings.emailAlerts}
                onChange={(v) => update('emailAlerts', v)}
              />
            </Field>
          </>
        )}
      </Section>

      {/* Export */}
      <Section icon={Download} title="Export Settings" description="Default export format and options">
        <Field label="Default Format" description="File format for data exports">
          <Select
            value={settings.exportFormat}
            onChange={(v) => update('exportFormat', v)}
            options={[
              { id: 'csv', label: 'CSV (.csv)' },
              { id: 'json', label: 'JSON (.json)' },
              { id: 'xlsx', label: 'Excel (.xlsx)' },
              { id: 'geojson', label: 'GeoJSON (.geojson)' },
            ]}
          />
        </Field>
        <Field label="Include Metadata" description="Add timestamps, model version, and headers to exports">
          <Toggle
            enabled={settings.includeMetadata}
            onChange={(v) => update('includeMetadata', v)}
          />
        </Field>
        <Field label="Auto Export" description="Automatically export data after each model run">
          <Toggle
            enabled={settings.autoExport}
            onChange={(v) => update('autoExport', v)}
          />
        </Field>
      </Section>

      {/* About */}
      <div className="dashboard-card p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
            <CloudRain className="w-[18px] h-[18px] text-blue-600" />
          </div>
          <div>
            <h3 className="text-[14px] font-bold text-gray-900">About</h3>
            <p className="text-[11px] text-gray-400">System information</p>
          </div>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: 'Version', value: '2.1.0' },
            { label: 'Model', value: 'Regime-Aware AI' },
            { label: 'Last Update', value: 'Sep 9, 2026' },
            { label: 'Grid Resolution', value: '1° x 1°' },
          ].map((item) => (
            <div key={item.label} className="bg-gray-50 rounded-lg p-3">
              <div className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider">{item.label}</div>
              <div className="text-[13px] font-bold text-gray-700 mt-0.5">{item.value}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
