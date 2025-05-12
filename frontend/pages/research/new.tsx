import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';

const academicFields = [
  'Computer Science',
  'Engineering',
  'Medicine',
  'Physics',
  'Chemistry',
  'Biology',
  'Mathematics',
  'Social Sciences',
  'Humanities',
  'Business',
  'Other'
];

const defaultSections = [
  'abstract',
  'introduction',
  'literature_review',
  'methodology',
  'results',
  'discussion',
  'conclusion',
  'references'
];

interface FormData {
  topic: string;
  keywords: string[];
  length: string;
  academic_field: string;
  paper_type: string;
  reference_style: string;
  target_audience: string;
  required_sections: string[];
  custom_sections: string[];
  additional_guidelines: string;
}

interface EditHistoryItem {
  timestamp: string;
  instructions: string;
  previous_content: string;
  new_content: string;
}

export default function ResearchPaperGenerator() {
  const [formData, setFormData] = useState<FormData>({
    topic: '',
    keywords: [],
    length: 'medium',
    academic_field: '',
    paper_type: 'experimental',
    reference_style: 'APA',
    target_audience: 'academic',
    required_sections: ['introduction', 'methodology', 'results', 'discussion', 'conclusion'],
    custom_sections: [],
    additional_guidelines: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [generatedContent, setGeneratedContent] = useState('');
  const [generatedTitles, setGeneratedTitles] = useState<string[]>([]);
  const [selectedTitle, setSelectedTitle] = useState('');
  const [showTitleSelection, setShowTitleSelection] = useState(false);
  const [paperId, setPaperId] = useState<string | null>(null);
  const [currentSection, setCurrentSection] = useState<string | null>(null);
  const [sectionContent, setSectionContent] = useState<Record<string, string>>({});
  const [confirmedSections, setConfirmedSections] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [editInstructions, setEditInstructions] = useState<Record<string, string>>({});
  const [isEditing, setIsEditing] = useState<Record<string, boolean>>({});
  const [editHistory, setEditHistory] = useState<Record<string, EditHistoryItem[]>>({});
  const [isAbstractConfirmed, setIsAbstractConfirmed] = useState(false);
  const [isTitleConfirmed, setIsTitleConfirmed] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      // Validate required fields
      if (!formData.topic || !formData.keywords) {
        throw new Error('Topic and keywords are required');
      }

      // Prepare data for title generation
      const requestData = {
        topic: formData.topic,
        keywords: formData.keywords,
        length: formData.length,
        academic_field: formData.academic_field,
        paper_type: formData.paper_type,
        reference_style: formData.reference_style,
        target_audience: formData.target_audience,
        required_sections: formData.required_sections,
        custom_sections: formData.custom_sections,
        additional_guidelines: formData.additional_guidelines
      };

      console.log('Submitting title generation request:', requestData);

      // First, generate titles
      const titleResponse = await fetch('http://localhost:8000/api/research-papers/titles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!titleResponse.ok) {
        const errorData = await titleResponse.json();
        throw new Error(errorData.detail || 'Failed to generate titles');
      }

      const responseData = await titleResponse.json();
      console.log('Received titles:', responseData);

      if (!responseData.titles || !Array.isArray(responseData.titles)) {
        throw new Error('Invalid response format from server');
      }

      // Show titles to user and wait for selection
      setGeneratedTitles(responseData.titles);
      setShowTitleSelection(true);
    } catch (err) {
      console.error('Error submitting form:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTitleSelection = async (title: string) => {
    setSelectedTitle(title);
    setSubmitting(false);
    setError(null);
  };

  const handleTitleConfirmation = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // Now generate the abstract with the selected title
      const response = await fetch('http://localhost:8000/api/research-papers/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          selected_title: selectedTitle,
          required_sections: formData.required_sections,
          custom_sections: formData.custom_sections
        }),
      });

      const data = await response.json();
      console.log('Response received:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to start paper generation');
      }

      setSuccess(true);
      setPaperId(data.paper_id);
      setCurrentSection(data.current_section);
      setIsTitleConfirmed(true);
      
    } catch (error: unknown) {
      console.error('Error starting paper generation:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setSubmitting(false);
    }
  };

  const generateNextSection = async (paperId: string) => {
    setIsGenerating(true);

    try {
      const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/generate-next`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate next section');
      }

      const data = await response.json();
      
      if (data.status === 'completed') {
        setIsGenerating(false);
        return;
      }

      setCurrentSection(data.current_section);
      setSectionContent(prev => ({
        ...prev,
        [data.current_section]: data.content
      }));

      // Continue generating next section
      await generateNextSection(paperId);
    } catch (error) {
      console.error('Error generating next section:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
      setIsGenerating(false);
    }
  };

  const handleSectionToggle = (section: string) => {
    setFormData(prev => ({
      ...prev,
      required_sections: prev.required_sections.includes(section)
        ? prev.required_sections.filter(s => s !== section)
        : [...prev.required_sections, section]
    }));
  };

  const addCustomSection = () => {
    if (formData.custom_sections.length > 0 && !formData.required_sections.includes(formData.custom_sections[0])) {
      setFormData(prev => ({
        ...prev,
        required_sections: [...prev.required_sections, prev.custom_sections[0]],
        custom_sections: []
      }));
    }
  };

  const handleEditSection = async (section: string) => {
    if (!paperId || !sectionContent[section]) return;
    
    setIsEditing(prev => ({ ...prev, [section]: true }));
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/edit-section`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          paper_id: paperId,
          section_name: section,
          current_content: sectionContent[section],
          edit_instructions: editInstructions[section]
        }),
      });

      const data = await response.json();
      console.log('Edit response:', data);

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to edit section');
      }

      // Update the section with the edited version
      setSectionContent(prev => ({
        ...prev,
        [section]: data.improved_content
      }));
      setEditHistory(prev => ({
        ...prev,
        [section]: [...(prev[section] || []), {
          timestamp: new Date().toISOString(),
          instructions: editInstructions[section],
          previous_content: sectionContent[section],
          new_content: data.improved_content
        }]
      }));
      setEditInstructions(prev => ({ ...prev, [section]: '' })); // Clear the edit instructions
    } catch (error) {
      console.error('Error editing section:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    } finally {
      setIsEditing(prev => ({ ...prev, [section]: false }));
    }
  };

  const fetchEditHistory = async () => {
    if (!paperId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/edit-history`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to fetch edit history');
      }
      
      // Convert the flat edit history array to a section-based structure
      const sectionHistory: Record<string, EditHistoryItem[]> = {};
      if (data.edit_history) {
        data.edit_history.forEach((edit: any) => {
          const section = edit.section_name || 'abstract'; // Default to abstract for backward compatibility
          if (!sectionHistory[section]) {
            sectionHistory[section] = [];
          }
          sectionHistory[section].push({
            timestamp: edit.timestamp,
            instructions: edit.instructions,
            previous_content: edit.previous_content,
            new_content: edit.new_content
          });
        });
      }
      setEditHistory(sectionHistory);
    } catch (error) {
      console.error('Error fetching edit history:', error);
    }
  };

  const handleConfirmAbstract = async () => {
    if (!paperId) return;
    
    try {
        // Update the paper status to indicate abstract is confirmed
        const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/confirm-abstract`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to confirm abstract');
        }

        setIsAbstractConfirmed(true);
        // You can add any additional logic here for what happens after confirmation
    } catch (error) {
        console.error('Error confirming abstract:', error);
        setError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  const handleGenerateSection = async (section: string) => {
    try {
      setIsGenerating(true);
      setCurrentSection(section);

      const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/generate-section`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          section,
          previous_sections: sectionContent,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate section');
      }

      const data = await response.json();
      
      // Update all sections with the new content
      setSectionContent(prev => ({
        ...prev,
        ...data.all_sections
      }));

      // Always update the references section if it exists
      if (data.references) {
        setSectionContent(prev => ({
          ...prev,
          references: data.references
        }));
      }
    } catch (error) {
      console.error('Error generating section:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate section');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirmSection = async (section: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/research-papers/${paperId}/confirm-section`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ section }),
      });

      if (!response.ok) {
        throw new Error('Failed to confirm section');
      }

      // Update confirmed sections
      setConfirmedSections(prev => [...prev, section]);
      
      // Move to next section
      const allSections = [...formData.required_sections, ...formData.custom_sections];
      const currentIndex = allSections.indexOf(section);
      if (currentIndex < allSections.length - 1) {
        setCurrentSection(allSections[currentIndex + 1]);
      }
    } catch (error) {
      console.error('Error confirming section:', error);
      setError(error instanceof Error ? error.message : 'An error occurred');
    }
  };

  useEffect(() => {
    if (paperId) {
        fetchEditHistory();
    }
  }, [paperId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100"
        >
          <div className="px-8 py-10">
            <div className="text-center mb-10">
              <h2 className="text-4xl font-bold text-gray-900 mb-2">
                AI Research Paper Generator
              </h2>
              <p className="text-gray-600">
                Fill in the details to generate your research paper
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <div className="space-y-2">
                <label htmlFor="topic" className="label">
                  Research Topic
                </label>
                <input
                  type="text"
                  id="topic"
                  value={formData.topic}
                  onChange={(e) => setFormData(prev => ({ ...prev, topic: e.target.value }))}
                  className={`input-field ${error ? 'input-error' : ''}`}
                  placeholder="Enter your research topic"
                />
                {error && (
                  <p className="error-message">{error}</p>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="keywords" className="label">
                  Keywords (comma-separated)
                </label>
                <input
                  type="text"
                  id="keywords"
                  value={formData.keywords.join(', ')}
                  onChange={(e) => setFormData(prev => ({ ...prev, keywords: e.target.value.split(',').map(k => k.trim()) }))}
                  className={`input-field ${error ? 'input-error' : ''}`}
                  placeholder="keyword1, keyword2, keyword3"
                />
                {error && (
                  <p className="error-message">{error}</p>
                )}
              </div>

              <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
                <div className="space-y-2">
                  <label htmlFor="length" className="label">
                    Paper Length
                  </label>
                  <select
                    id="length"
                    value={formData.length}
                    onChange={(e) => setFormData(prev => ({ ...prev, length: e.target.value }))}
                    className="input-field"
                  >
                    <option value="short">Short (5-10 pages)</option>
                    <option value="medium">Medium (10-20 pages)</option>
                    <option value="long">Long (20+ pages)</option>
                  </select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="academic_field" className="label">
                    Academic Field
                  </label>
                  <select
                    id="academic_field"
                    value={formData.academic_field}
                    onChange={(e) => setFormData(prev => ({ ...prev, academic_field: e.target.value }))}
                    className={`input-field ${error ? 'input-error' : ''}`}
                  >
                    <option value="">Select a field</option>
                    {academicFields.map(field => (
                      <option key={field} value={field}>{field}</option>
                    ))}
                  </select>
                  {error && (
                    <p className="error-message">{error}</p>
                  )}
                </div>
              </div>

              <div className="space-y-2">
                <label className="label">
                  Paper Type
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {['review', 'experimental', 'conceptual'].map(type => (
                    <label key={type} className="checkbox-label">
                      <input
                        type="radio"
                        name="paper_type"
                        value={type}
                        checked={formData.paper_type === type}
                        onChange={(e) => setFormData(prev => ({ ...prev, paper_type: e.target.value }))}
                        className="checkbox-input"
                      />
                      <span className="ml-2 capitalize">{type}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="label">Required Sections</label>
                <div className="grid grid-cols-2 gap-4">
                  {defaultSections.map(section => (
                    <label key={section} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.required_sections.includes(section)}
                        onChange={() => handleSectionToggle(section)}
                        className="checkbox"
                      />
                      <span className="text-gray-700 capitalize">{section.replace('_', ' ')}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="space-y-4">
                <label className="label">Custom Sections</label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={formData.custom_sections[0] || ''}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      custom_sections: [e.target.value]
                    }))}
                    className="input-field"
                    placeholder="Enter custom section name"
                  />
                  <button
                    type="button"
                    onClick={addCustomSection}
                    className="btn-secondary"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="reference_style" className="label">
                  Reference Style
                </label>
                <select
                  id="reference_style"
                  value={formData.reference_style}
                  onChange={(e) => setFormData(prev => ({ ...prev, reference_style: e.target.value }))}
                  className="input-field"
                >
                  <option value="apa">APA</option>
                  <option value="ieee">IEEE</option>
                  <option value="mla">MLA</option>
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="guidelines" className="label">
                  Additional Guidelines (Optional)
                </label>
                <textarea
                  id="guidelines"
                  value={formData.additional_guidelines}
                  onChange={(e) => setFormData(prev => ({ ...prev, additional_guidelines: e.target.value }))}
                  className="input-field"
                  rows={4}
                  placeholder="Any specific requirements or guidelines..."
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="target_audience" className="label">
                  Target Audience (Optional)
                </label>
                <input
                  type="text"
                  id="target_audience"
                  value={formData.target_audience}
                  onChange={(e) => setFormData(prev => ({ ...prev, target_audience: e.target.value }))}
                  className="input-field"
                  placeholder="e.g., Undergraduate students, Researchers, etc."
                />
              </div>

              <div className="flex justify-end pt-4">
                <motion.button
                  type="submit"
                  disabled={submitting}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="submit-button"
                >
                  {submitting ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Submitting...
                    </span>
                  ) : (
                    'Generate Titles'
                  )}
                </motion.button>
              </div>
            </form>

            {!showTitleSelection && !submitting && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="mt-12 text-center"
              >
                <p className="text-gray-600 mb-4">Fill out the form above to generate paper titles</p>
                <motion.div
                  animate={{ y: [0, 10, 0] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                  className="inline-block"
                >
                  <svg className="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                  </svg>
                </motion.div>
              </motion.div>
            )}
          </div>
        </motion.div>

        {showTitleSelection && generatedTitles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-8 bg-white shadow rounded-lg p-6"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Step 1: Choose Your Paper Title</h2>
            <p className="text-gray-600 mb-6">Select one of the generated titles to proceed with paper generation</p>
            
            <div className="space-y-3">
              {generatedTitles.map((title, index) => (
                <motion.button
                  key={index}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => handleTitleSelection(title)}
                  className={`w-full text-left p-3 rounded-lg border ${
                    selectedTitle === title
                      ? 'border-indigo-500 bg-indigo-50'
                      : 'border-gray-200 hover:border-indigo-300'
                  }`}
                >
                  <p className="text-base font-medium text-gray-900">{title}</p>
                </motion.button>
              ))}
            </div>
            
            {selectedTitle && !isTitleConfirmed && (
              <div className="mt-6 flex justify-end">
                <motion.button
                  onClick={handleTitleConfirmation}
                  disabled={submitting}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="submit-button"
                >
                  {submitting ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Confirming...
                    </span>
                  ) : (
                    'Confirm Title'
                  )}
                </motion.button>
              </div>
            )}
          </motion.div>
        )}

        {success && generatedContent && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-8 bg-white shadow rounded-lg p-6"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Generated Research Paper</h2>
            <div className="prose max-w-none">
              <pre className="whitespace-pre-wrap font-sans text-gray-800">
                {generatedContent}
              </pre>
            </div>
            
            {/* References Section */}
            {sectionContent.references && (
              <div className="mt-8 border-t border-gray-200 pt-6">
                <h3 className="text-xl font-bold text-gray-900 mb-4">References</h3>
                <div className="space-y-2">
                  {sectionContent.references.split('\n').map((ref, index) => (
                    <p key={index} className="text-sm text-gray-700">
                      {ref}
                    </p>
                  ))}
                </div>
              </div>
            )}
            
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => {
                  const blob = new Blob([generatedContent], { type: 'text/plain' });
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `${formData.topic.toLowerCase().replace(/\s+/g, '-')}-research-paper.txt`;
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  document.body.removeChild(a);
                }}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Download Paper
              </button>
            </div>
          </motion.div>
        )}

        {/* Section Generation UI */}
        {isTitleConfirmed && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mt-8 bg-white shadow rounded-lg p-6"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Step 2: Generate Sections</h2>
            
            {/* Show all sections in sequence */}
            {[...formData.required_sections, ...formData.custom_sections].map((section, index) => {
              const isCurrentSection = section === currentSection;
              const isGenerated = sectionContent[section] !== undefined;
              const isConfirmed = confirmedSections.includes(section);
              
              return (
                <motion.div
                  key={section}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="mb-8"
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">
                      {section.replace('_', ' ')}
                      {isConfirmed && (
                        <span className="ml-2 text-green-500">
                          ✓
                        </span>
                      )}
                    </h3>
                    {isGenerated && !isConfirmed && (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleGenerateSection(section)}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          Regenerate
                        </button>
                        <button
                          onClick={() => handleConfirmSection(section)}
                          className="px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                        >
                          Confirm
                        </button>
                      </div>
                    )}
                  </div>
                  
                  {isGenerated ? (
                    <div className="space-y-4">
                      <div className="p-4 bg-gray-50 rounded-lg">
                        {sectionContent[section]}
                      </div>
                      
                      <div className="mt-4">
                        <h4 className="text-lg font-semibold mb-2">Edit {section.replace('_', ' ')}</h4>
                        <div className="space-y-4">
                          <div>
                            <label htmlFor={`editInstructions-${section}`} className="block text-sm font-medium text-gray-700">
                              Edit Instructions
                            </label>
                            <textarea
                              id={`editInstructions-${section}`}
                              value={editInstructions[section] || ''}
                              onChange={(e) => setEditInstructions(prev => ({ ...prev, [section]: e.target.value }))}
                              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                              rows={4}
                              placeholder={`Enter your instructions for editing the ${section.replace('_', ' ')}...`}
                            />
                          </div>
                          <button
                            onClick={() => handleEditSection(section)}
                            disabled={isEditing[section] || !editInstructions[section]?.trim()}
                            className={`inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white ${
                              isEditing[section] || !editInstructions[section]?.trim()
                                ? 'bg-indigo-300 cursor-not-allowed'
                                : 'bg-indigo-600 hover:bg-indigo-700'
                            }`}
                          >
                            {isEditing[section] ? (
                              <span className="flex items-center">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Editing...
                              </span>
                            ) : (
                              `Edit ${section.replace('_', ' ')}`
                            )}
                          </button>
                        </div>
                      </div>

                      {editHistory[section]?.length > 0 && (
                        <div className="mt-4">
                          <h4 className="text-lg font-semibold mb-2">Edit History</h4>
                          <div className="space-y-4">
                            {editHistory[section].map((edit, index) => (
                              <div key={index} className="border rounded-lg p-4">
                                <div className="flex justify-between items-start mb-2">
                                  <span className="text-sm text-gray-500">
                                    {new Date(edit.timestamp).toLocaleString()}
                                  </span>
                                </div>
                                <div className="mb-2">
                                  <h4 className="font-medium text-gray-700">Instructions:</h4>
                                  <p className="text-gray-600">{edit.instructions}</p>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                  <div>
                                    <h4 className="font-medium text-gray-700">Previous Version:</h4>
                                    <p className="text-gray-600 whitespace-pre-wrap">{edit.previous_content}</p>
                                  </div>
                                  <div>
                                    <h4 className="font-medium text-gray-700">New Version:</h4>
                                    <p className="text-gray-600 whitespace-pre-wrap">{edit.new_content}</p>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    isCurrentSection && (
                      <div className="flex justify-end">
                        <button
                          onClick={() => handleGenerateSection(section)}
                          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        >
                          Generate {section.replace('_', ' ')}
                        </button>
                      </div>
                    )
                  )}
                </motion.div>
              );
            })}

            {/* Always show References section */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="mt-8 border-t border-gray-200 pt-6"
            >
              <h3 className="text-lg font-semibold mb-4">References</h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                {sectionContent.references && typeof sectionContent.references === 'string' ? (
                  <div className="space-y-2">
                    {sectionContent.references
                      .split('\n')
                      .filter(ref => ref.trim()) // Remove empty lines
                      .map((ref, index) => (
                        <p key={index} className="text-sm text-gray-700">
                          {ref}
                        </p>
                      ))}
                  </div>
                ) : (
                  <p className="text-gray-500 italic">References will appear here as they are used in the paper.</p>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}

        {sectionContent.abstract && !isAbstractConfirmed && (
          <div className="mt-8 flex justify-end">
            <motion.button
              onClick={handleConfirmAbstract}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <svg className="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Confirm Abstract
            </motion.button>
          </div>
        )}

        {isAbstractConfirmed && (
          <div className="mt-4 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center">
              <svg className="h-5 w-5 text-green-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-800 font-medium">Abstract confirmed! You can proceed to the next step.</span>
            </div>
          </div>
        )}

        {isGenerating && (
          <div className="mt-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600">Generating {currentSection}...</p>
          </div>
        )}
      </div>
    </div>
  );
} 