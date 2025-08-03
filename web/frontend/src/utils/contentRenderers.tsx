import React from 'react';
import MarkdownRenderer from '../components/MarkdownRenderer';

// Type definitions for advocacy and skepticism content structures
interface AdvocacyItem {
  title?: string;
  description?: string;
}

interface ConcernItem {
  concern?: string;
  response?: string;
}

interface AdvocacyStructure {
  strengths?: Array<AdvocacyItem | string>;
  opportunities?: Array<AdvocacyItem | string>;
  addressing_concerns?: Array<ConcernItem | string>;
}

interface SkepticismItem {
  title?: string;
  description?: string;
}

interface AssumptionItem {
  assumption?: string;
  concern?: string;
}

interface ConsiderationItem {
  aspect?: string;
  importance?: string;
}

interface SkepticismStructure {
  critical_flaws?: Array<SkepticismItem | string>;
  risks_and_challenges?: Array<SkepticismItem | string>;
  questionable_assumptions?: Array<AssumptionItem | string>;
  missing_considerations?: Array<ConsiderationItem | string>;
}

type ContentInput = string | AdvocacyStructure | SkepticismStructure;

// Configuration for rendering a section
interface SectionConfig {
  title: string;
  bulletColor: string;
  items: Array<any>;
  renderItem: (item: any) => React.ReactNode;
}

/**
 * Renders a list section with consistent styling
 */
const renderSection = ({ title, bulletColor, items, renderItem }: SectionConfig) => {
  if (!items || items.length === 0) return null;
  
  return (
    <div>
      <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
      <ul className="space-y-2">
        {items.map((item, idx) => (
          <li key={idx} className="flex items-start">
            <span className={`${bulletColor} mr-2`}>•</span>
            <div>{renderItem(item)}</div>
          </li>
        ))}
      </ul>
    </div>
  );
};

/**
 * Safely renders an advocacy item with proper type checking
 */
const renderAdvocacyItem = (item: AdvocacyItem | string): React.ReactNode => {
  if (typeof item === 'string') {
    return item;
  }
  
  if (typeof item === 'object' && item !== null) {
    const title = item.title;
    const description = item.description;
    
    if (title && description) {
      return (
        <>
          <strong>{title}:</strong> {description}
        </>
      );
    } else if (title) {
      return <strong>{title}</strong>;
    } else if (description) {
      return description;
    }
  }
  
  return null;
};

/**
 * Safely renders a concern item with proper type checking
 */
const renderConcernItem = (item: ConcernItem | string): React.ReactNode => {
  if (typeof item === 'string') {
    return item;
  }
  
  if (typeof item === 'object' && item !== null && item.concern && item.response) {
    return (
      <>
        <strong>{item.concern}:</strong> {item.response}
      </>
    );
  }
  
  return null;
};

/**
 * Safely renders a skepticism item with proper type checking
 */
const renderSkepticismItem = (item: SkepticismItem | string): React.ReactNode => {
  if (typeof item === 'string') {
    return item;
  }
  
  if (typeof item === 'object' && item !== null) {
    const title = item.title;
    const description = item.description;
    
    if (title && description) {
      return (
        <>
          <strong>{title}:</strong> {description}
        </>
      );
    } else if (title) {
      return <strong>{title}</strong>;
    } else if (description) {
      return description;
    }
  }
  
  return null;
};

/**
 * Safely renders an assumption item with proper type checking
 */
const renderAssumptionItem = (item: AssumptionItem | string): React.ReactNode => {
  if (typeof item === 'string') {
    return item;
  }
  
  if (typeof item === 'object' && item !== null && item.assumption) {
    return (
      <>
        <strong>{item.assumption}:</strong> {item.concern || ''}
      </>
    );
  }
  
  return null;
};

/**
 * Safely renders a consideration item with proper type checking
 */
const renderConsiderationItem = (item: ConsiderationItem | string): React.ReactNode => {
  if (typeof item === 'string') {
    return item;
  }
  
  if (typeof item === 'object' && item !== null && item.aspect) {
    return (
      <>
        <strong>{item.aspect}:</strong> {item.importance || ''}
      </>
    );
  }
  
  return null;
};

/**
 * Renders advocacy content which can be either a JSON string or plain text
 * @param advocacy - The advocacy content (JSON string or plain text)
 * @returns React component rendering the content
 */
export const renderAdvocacyContent = (advocacy: ContentInput) => {
  if (!advocacy) return <MarkdownRenderer content="" />;
  
  // Check if it's a JSON string
  if (typeof advocacy === 'string') {
    try {
      const parsed = JSON.parse(advocacy);
      if (parsed && typeof parsed === 'object' && 'strengths' in parsed) {
        const advocacyData = parsed as AdvocacyStructure;
        
        // It's structured JSON - render it nicely
        return (
          <div className="space-y-4">
            {renderSection({
              title: 'STRENGTHS:',
              bulletColor: 'text-green-500',
              items: advocacyData.strengths || [],
              renderItem: renderAdvocacyItem
            })}
            
            {renderSection({
              title: 'OPPORTUNITIES:',
              bulletColor: 'text-blue-500',
              items: advocacyData.opportunities || [],
              renderItem: renderAdvocacyItem
            })}
            
            {renderSection({
              title: 'ADDRESSING CONCERNS:',
              bulletColor: 'text-yellow-600',
              items: advocacyData.addressing_concerns || [],
              renderItem: renderConcernItem
            })}
          </div>
        );
      }
    } catch (e) {
      // Not JSON or parsing failed - treat as markdown
    }
  }
  
  // Default: render as markdown
  return <MarkdownRenderer content={String(advocacy)} />;
};

/**
 * Renders skepticism content which can be either a JSON string or plain text
 * @param skepticism - The skepticism content (JSON string or plain text)
 * @returns React component rendering the content
 */
export const renderSkepticismContent = (skepticism: ContentInput) => {
  if (!skepticism) return <MarkdownRenderer content="" />;
  
  // Check if it's a JSON string
  if (typeof skepticism === 'string') {
    try {
      const parsed = JSON.parse(skepticism);
      if (parsed && typeof parsed === 'object' && 'critical_flaws' in parsed) {
        const skepticismData = parsed as SkepticismStructure;
        
        // It's structured JSON - render it nicely
        return (
          <div className="space-y-4">
            {renderSection({
              title: 'CRITICAL FLAWS:',
              bulletColor: 'text-red-500',
              items: skepticismData.critical_flaws || [],
              renderItem: renderSkepticismItem
            })}
            
            {renderSection({
              title: 'RISKS & CHALLENGES:',
              bulletColor: 'text-orange-500',
              items: skepticismData.risks_and_challenges || [],
              renderItem: renderSkepticismItem
            })}
            
            {renderSection({
              title: 'QUESTIONABLE ASSUMPTIONS:',
              bulletColor: 'text-yellow-600',
              items: skepticismData.questionable_assumptions || [],
              renderItem: renderAssumptionItem
            })}
            
            {renderSection({
              title: 'MISSING CONSIDERATIONS:',
              bulletColor: 'text-gray-600',
              items: skepticismData.missing_considerations || [],
              renderItem: renderConsiderationItem
            })}
          </div>
        );
      }
    } catch (e) {
      // Not JSON or parsing failed - treat as markdown
    }
  }
  
  // Default: render as markdown
  return <MarkdownRenderer content={String(skepticism)} />;
};