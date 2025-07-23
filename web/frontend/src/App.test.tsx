import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Basic test to ensure tests run
describe('App Tests', () => {
  test('basic test setup works', () => {
    // Simple test to ensure Jest is configured correctly
    expect(true).toBe(true);
  });

  test('React Testing Library works', () => {
    render(<div data-testid="test-element">Test</div>);
    const element = screen.getByTestId('test-element');
    expect(element).toBeInTheDocument();
    expect(element).toHaveTextContent('Test');
  });
});