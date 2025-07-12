import React, { useState, useEffect } from 'react';
import api from '../api';

interface FormData {
  theme: string;
  constraints: string;
  num_top_candidates: number;
  enable_novelty_filter: boolean;
  novelty_threshold: number;
  temperature_preset: string | null;
  temperature: number | null;
  enhanced_reasoning: boolean;
  multi_dimensional_eval: boolean;
  logical_inference: boolean;
  verbose: boolean;
}

interface TemperaturePreset {
  [key: string]: {
    idea_generation: number;
    evaluation: number;
    advocacy: number;
    skepticism: number;
    description: string;
  };
}

interface IdeaGenerationFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
}

const IdeaGenerationForm: React.FC<IdeaGenerationFormProps> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<FormData>({
    theme: '',
    constraints: '',
    num_top_candidates: 2,
    enable_novelty_filter: true,
    novelty_threshold: 0.8,
    temperature_preset: 'balanced',
    temperature: null,
    enhanced_reasoning: false,
    multi_dimensional_eval: true,  // Always enabled
    logical_inference: false,
    verbose: false,
  });

  const [temperaturePresets, setTemperaturePresets] = useState<TemperaturePreset>({});
  const [useCustomTemperature, setUseCustomTemperature] = useState(false);

  // Load temperature presets
  useEffect(() => {
    const loadPresets = async () => {
      try {
        const response = await api.get('/api/temperature-presets');
        console.log('Temperature presets response:', response.data);
        if (response.data.status === 'success' && response.data.presets) {
          setTemperaturePresets(response.data.presets);
        }
      } catch (error) {
        console.error('Failed to load temperature presets:', error);
      }
    };
    loadPresets();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData(prev => ({ ...prev, [name]: checked }));
    } else if (type === 'number') {
      setFormData(prev => ({ ...prev, [name]: parseFloat(value) || 0 }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prepare submission data
    const submissionData = {
      ...formData,
      temperature: useCustomTemperature ? formData.temperature : null,
      temperature_preset: useCustomTemperature ? null : formData.temperature_preset,
    };
    
    onSubmit(submissionData);
  };

  const selectedPreset = formData.temperature_preset ? temperaturePresets[formData.temperature_preset] : null;

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Generate Ideas</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Theme */}
        <div>
          <label htmlFor="theme" className="block text-sm font-medium text-gray-700">
            Theme *
          </label>
          <input
            type="text"
            id="theme"
            name="theme"
            required
            value={formData.theme}
            onChange={handleInputChange}
            placeholder="e.g., Sustainable urban living"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* Constraints */}
        <div>
          <label htmlFor="constraints" className="block text-sm font-medium text-gray-700">
            Constraints *
          </label>
          <textarea
            id="constraints"
            name="constraints"
            required
            rows={3}
            value={formData.constraints}
            onChange={handleInputChange}
            placeholder="e.g., Budget-friendly, implementable within 5 years, community-focused"
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          />
        </div>

        {/* Number of Candidates */}
        <div>
          <label htmlFor="num_top_candidates" className="block text-sm font-medium text-gray-700">
            Number of Top Ideas
          </label>
          <select
            id="num_top_candidates"
            name="num_top_candidates"
            value={formData.num_top_candidates}
            onChange={handleInputChange}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          >
            {[1, 2, 3, 4, 5].map(num => (
              <option key={num} value={num}>{num}</option>
            ))}
          </select>
        </div>

        {/* Temperature Control */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Creativity Level
          </label>
          <div className="space-y-3">
            <div className="flex items-center">
              <input
                type="radio"
                id="preset-temp"
                name="temperature-mode"
                checked={!useCustomTemperature}
                onChange={() => setUseCustomTemperature(false)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <label htmlFor="preset-temp" className="ml-2 text-sm text-gray-700">
                Use preset
              </label>
            </div>
            
            {!useCustomTemperature && (
              <select
                name="temperature_preset"
                value={formData.temperature_preset || 'balanced'}
                onChange={handleInputChange}
                className="ml-6 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="">Select a preset...</option>
                {Object.keys(temperaturePresets).length > 0 ? (
                  Object.entries(temperaturePresets).map(([key, preset]) => (
                    <option key={key} value={key}>
                      {key.charAt(0).toUpperCase() + key.slice(1)} - {(preset as any).description || `${key} preset`}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="conservative">Conservative - Low creativity, focused ideas</option>
                    <option value="balanced">Balanced - Moderate creativity (default)</option>
                    <option value="creative">Creative - High creativity, innovative ideas</option>
                    <option value="wild">Wild - Maximum creativity, experimental ideas</option>
                  </>
                )}
              </select>
            )}

            <div className="flex items-center">
              <input
                type="radio"
                id="custom-temp"
                name="temperature-mode"
                checked={useCustomTemperature}
                onChange={() => setUseCustomTemperature(true)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
              />
              <label htmlFor="custom-temp" className="ml-2 text-sm text-gray-700">
                Custom temperature
              </label>
            </div>
            
            {useCustomTemperature && (
              <input
                type="number"
                name="temperature"
                min="0"
                max="2"
                step="0.1"
                value={formData.temperature || 0.7}
                onChange={handleInputChange}
                className="ml-6 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            )}
          </div>
          
          {selectedPreset && !useCustomTemperature && (
            <div className="mt-2 text-xs text-gray-500">
              Ideas: {selectedPreset.idea_generation}, Evaluation: {selectedPreset.evaluation}, 
              Advocacy: {selectedPreset.advocacy}, Skepticism: {selectedPreset.skepticism}
            </div>
          )}
        </div>

        {/* Enhanced Features */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Enhanced Features
          </label>
          <div className="space-y-3">
            <div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="enhanced_reasoning"
                  name="enhanced_reasoning"
                  checked={formData.enhanced_reasoning}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="enhanced_reasoning" className="ml-2 text-sm text-gray-700 font-medium">
                  Enhanced Reasoning
                </label>
              </div>
              <p className="ml-6 mt-1 text-xs text-gray-500">
                Enables context-aware agents that reference conversation history for more informed and coherent decisions
              </p>
            </div>
            
            <div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="logical_inference"
                  name="logical_inference"
                  checked={formData.logical_inference}
                  onChange={handleInputChange}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="logical_inference" className="ml-2 text-sm text-gray-700 font-medium">
                  Logical Inference
                </label>
              </div>
              <p className="ml-6 mt-1 text-xs text-gray-500">
                Applies formal reasoning chains with confidence scoring and consistency analysis for more rigorous idea validation
              </p>
            </div>
          </div>
        </div>

        {/* Novelty Filter */}
        <div>
          <div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="enable_novelty_filter"
                name="enable_novelty_filter"
                checked={formData.enable_novelty_filter}
                onChange={handleInputChange}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="enable_novelty_filter" className="ml-2 text-sm text-gray-700 font-medium">
                Enable Novelty Filter
              </label>
            </div>
            <p className="ml-6 mt-1 text-xs text-gray-500">
              Filters out duplicate or overly similar ideas to ensure diverse and unique suggestions
            </p>
          </div>
          
          {formData.enable_novelty_filter && (
            <div className="mt-2 ml-6">
              <label htmlFor="novelty_threshold" className="block text-xs text-gray-600">
                Similarity Threshold: {formData.novelty_threshold}
              </label>
              <input
                type="range"
                id="novelty_threshold"
                name="novelty_threshold"
                min="0"
                max="1"
                step="0.1"
                value={formData.novelty_threshold}
                onChange={handleInputChange}
                className="mt-1 w-full"
              />
            </div>
          )}
        </div>

        {/* Verbose Mode */}
        <div>
          <div className="flex items-center">
            <input
              type="checkbox"
              id="verbose"
              name="verbose"
              checked={formData.verbose}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="verbose" className="ml-2 text-sm text-gray-700 font-medium">
              Verbose Mode
            </label>
          </div>
          <p className="ml-6 mt-1 text-xs text-gray-500">
            Provides detailed logging and step-by-step progress information during idea generation
          </p>
        </div>

        {/* Submit Button */}
        <div>
          <button
            type="submit"
            disabled={isLoading || !formData.theme || !formData.constraints}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating Ideas...
              </>
            ) : (
              'Generate Ideas'
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default IdeaGenerationForm;