import React from 'react';
import MarkdownRenderer from '../components/MarkdownRenderer';

/**
 * Renders advocacy content which can be either a JSON string or plain text
 * @param advocacy - The advocacy content (JSON string or plain text)
 * @returns React component rendering the content
 */
export const renderAdvocacyContent = (advocacy: any) => {
  if (!advocacy) return <MarkdownRenderer content="" />;
  
  // Check if it's a JSON string
  if (typeof advocacy === 'string') {
    try {
      const parsed = JSON.parse(advocacy);
      if (parsed && typeof parsed === 'object' && 'strengths' in parsed) {
        // It's structured JSON - render it nicely
        return (
          <div className="space-y-4">
            {parsed.strengths && parsed.strengths.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">STRENGTHS:</h4>
                <ul className="space-y-2">
                  {parsed.strengths.map((strength: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-green-500 mr-2">•</span>
                      <div>
                        {strength.title && <strong>{strength.title}:</strong>} {strength.description || strength}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {parsed.opportunities && parsed.opportunities.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">OPPORTUNITIES:</h4>
                <ul className="space-y-2">
                  {parsed.opportunities.map((opportunity: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-blue-500 mr-2">•</span>
                      <div>
                        {opportunity.title && <strong>{opportunity.title}:</strong>} {opportunity.description || opportunity}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {parsed.addressing_concerns && parsed.addressing_concerns.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">ADDRESSING CONCERNS:</h4>
                <ul className="space-y-2">
                  {parsed.addressing_concerns.map((concern: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-yellow-600 mr-2">•</span>
                      <div>
                        {concern.concern && concern.response ? (
                          <>
                            <strong>{concern.concern}:</strong> {concern.response}
                          </>
                        ) : (
                          concern
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      }
    } catch (e) {
      // Not JSON or parsing failed - treat as markdown
    }
  }
  // Default: render as markdown
  return <MarkdownRenderer content={advocacy} />;
};

/**
 * Renders skepticism content which can be either a JSON string or plain text
 * @param skepticism - The skepticism content (JSON string or plain text)
 * @returns React component rendering the content
 */
export const renderSkepticismContent = (skepticism: any) => {
  if (!skepticism) return <MarkdownRenderer content="" />;
  
  // Check if it's a JSON string
  if (typeof skepticism === 'string') {
    try {
      const parsed = JSON.parse(skepticism);
      if (parsed && typeof parsed === 'object' && 'critical_flaws' in parsed) {
        // It's structured JSON - render it nicely
        return (
          <div className="space-y-4">
            {parsed.critical_flaws && parsed.critical_flaws.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">CRITICAL FLAWS:</h4>
                <ul className="space-y-2">
                  {parsed.critical_flaws.map((flaw: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-red-500 mr-2">•</span>
                      <div>
                        {flaw.title && <strong>{flaw.title}:</strong>} {flaw.description || flaw}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {parsed.risks_and_challenges && parsed.risks_and_challenges.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">RISKS & CHALLENGES:</h4>
                <ul className="space-y-2">
                  {parsed.risks_and_challenges.map((risk: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-orange-500 mr-2">•</span>
                      <div>
                        {risk.title && <strong>{risk.title}:</strong>} {risk.description || risk}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {parsed.questionable_assumptions && parsed.questionable_assumptions.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">QUESTIONABLE ASSUMPTIONS:</h4>
                <ul className="space-y-2">
                  {parsed.questionable_assumptions.map((assumption: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-yellow-600 mr-2">•</span>
                      <div>
                        {assumption.assumption && <strong>{assumption.assumption}:</strong>} {assumption.concern}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            {parsed.missing_considerations && parsed.missing_considerations.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">MISSING CONSIDERATIONS:</h4>
                <ul className="space-y-2">
                  {parsed.missing_considerations.map((consideration: any, idx: number) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-gray-600 mr-2">•</span>
                      <div>
                        {consideration.aspect && <strong>{consideration.aspect}:</strong>} {consideration.importance}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        );
      }
    } catch (e) {
      // Not JSON or parsing failed - treat as markdown
    }
  }
  // Default: render as markdown
  return <MarkdownRenderer content={skepticism} />;
};