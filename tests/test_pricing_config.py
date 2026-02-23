import unittest
import importlib.util
import sys

# Helper to load the module directly, bypassing package imports.
# This is necessary because the development environment lacks some core dependencies
# (like google-genai and pydantic) required by the top-level madspark package.
# Loading the file directly avoids triggering these imports.
def load_pricing_config():
    spec = importlib.util.spec_from_file_location("pricing_config", "src/madspark/utils/pricing_config.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["pricing_config"] = module
    spec.loader.exec_module(module)
    return module

class TestPricingConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pricing_config = load_pricing_config()
        cls.get_token_cost = staticmethod(cls.pricing_config.get_token_cost)
        cls.estimate_cost = staticmethod(cls.pricing_config.estimate_cost)
        cls.TOKEN_COSTS = cls.pricing_config.TOKEN_COSTS
        cls.DEFAULT_PRICING_MODEL = cls.pricing_config.DEFAULT_PRICING_MODEL
        cls.DEFAULT_OUTPUT_RATIO = cls.pricing_config.DEFAULT_OUTPUT_RATIO

    def test_get_token_cost_valid_model_input(self):
        """Test getting cost for a valid model and input type."""
        model = "gemini-3-flash-preview"
        cost = self.get_token_cost(model, "input")
        self.assertEqual(cost, self.TOKEN_COSTS[model]["input"])

    def test_get_token_cost_valid_model_output(self):
        """Test getting cost for a valid model and output type."""
        model = "gemini-3-flash-preview"
        cost = self.get_token_cost(model, "output")
        self.assertEqual(cost, self.TOKEN_COSTS[model]["output"])

    def test_get_token_cost_unknown_model_fallback(self):
        """Test fallback to default model for unknown model."""
        unknown_model = "unknown-model-v1"
        cost = self.get_token_cost(unknown_model, "input")
        expected_cost = self.TOKEN_COSTS[self.DEFAULT_PRICING_MODEL]["input"]
        self.assertEqual(cost, expected_cost)

    def test_get_token_cost_invalid_token_type(self):
        """Test handling of invalid token type."""
        # Should raise ValueError for invalid token type
        with self.assertRaises(ValueError):
            self.get_token_cost("gemini-3-flash-preview", "invalid_type")

    def test_estimate_cost_explicit_output(self):
        """Test cost estimation with explicit output tokens."""
        model = "gemini-3-flash-preview"
        input_tokens = 1000
        output_tokens = 500

        expected_cost = (
            (self.TOKEN_COSTS[model]["input"] * (input_tokens / 1000)) +
            (self.TOKEN_COSTS[model]["output"] * (output_tokens / 1000))
        )

        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.assertAlmostEqual(cost, expected_cost)

    def test_estimate_cost_implicit_output(self):
        """Test cost estimation using default output ratio."""
        model = "gemini-3-flash-preview"
        input_tokens = 1000
        # Implicit output tokens = input_tokens * DEFAULT_OUTPUT_RATIO
        output_tokens = int(input_tokens * self.DEFAULT_OUTPUT_RATIO)

        expected_cost = (
            (self.TOKEN_COSTS[model]["input"] * (input_tokens / 1000)) +
            (self.TOKEN_COSTS[model]["output"] * (output_tokens / 1000))
        )

        cost = self.estimate_cost(model, input_tokens)
        self.assertAlmostEqual(cost, expected_cost)

    def test_estimate_cost_unknown_model(self):
        """Test cost estimation with unknown model (fallback)."""
        model = "unknown-model"
        input_tokens = 1000
        output_tokens = 500

        # Should use default model pricing
        default_model = self.DEFAULT_PRICING_MODEL
        expected_cost = (
            (self.TOKEN_COSTS[default_model]["input"] * (input_tokens / 1000)) +
            (self.TOKEN_COSTS[default_model]["output"] * (output_tokens / 1000))
        )

        cost = self.estimate_cost(model, input_tokens, output_tokens)
        self.assertAlmostEqual(cost, expected_cost)

if __name__ == "__main__":
    unittest.main()
