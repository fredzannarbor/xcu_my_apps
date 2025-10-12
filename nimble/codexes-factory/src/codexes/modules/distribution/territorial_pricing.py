# src/codexes/modules/distribution/territorial_pricing.py

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
import json
import os

# Try to import requests, but provide fallback if not available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests module not available, using fallback exchange rates")

@dataclass
class TerritorialPricingConfig:
    """Configuration for territorial pricing strategies."""
    base_currency: str = "USD"
    wiggle_room_percent: float = 5.0  # Extra % increase for unexpected variations
    market_access_fee_usd: float = 0.0  # Extra USD surcharge
    cache_duration_hours: int = 24  # How long to cache exchange rates
    fallback_multipliers: Dict[str, float] = None  # Fallback if API fails
    
    def __post_init__(self):
        if self.fallback_multipliers is None:
            self.fallback_multipliers = {
                "USD": 1.0,
                "GBP": 0.79,
                "EUR": 0.85,
                "CAD": 1.25,
                "AUD": 1.35,
                "JPY": 110.0,
                "CHF": 0.92,
                "SEK": 8.5,
                "NOK": 8.8,
                "DKK": 6.3
            }

@dataclass
class ExchangeRateData:
    """Exchange rate data with timestamp."""
    rates: Dict[str, float]
    timestamp: datetime
    source: str = "api"

class TerritorialPricingStrategy:
    """Advanced territorial pricing strategy with dynamic exchange rates."""
    
    def __init__(self, config: TerritorialPricingConfig = None):
        self.config = config or TerritorialPricingConfig()
        self.cache_file = "cache/exchange_rates.json"
        self.cached_rates: Optional[ExchangeRateData] = None
        self.logger = logging.getLogger(__name__)
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        # Load cached rates on initialization
        self._load_cached_rates()
    
    def _load_cached_rates(self):
        """Load cached exchange rates from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.cached_rates = ExchangeRateData(
                        rates=data['rates'],
                        timestamp=datetime.fromisoformat(data['timestamp']),
                        source=data.get('source', 'cache')
                    )
                    self.logger.info(f"Loaded cached exchange rates from {self.cached_rates.timestamp}")
        except Exception as e:
            self.logger.warning(f"Failed to load cached exchange rates: {e}")
            self.cached_rates = None
    
    def _save_cached_rates(self, rates_data: ExchangeRateData):
        """Save exchange rates to cache file."""
        try:
            cache_data = {
                'rates': rates_data.rates,
                'timestamp': rates_data.timestamp.isoformat(),
                'source': rates_data.source
            }
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            self.logger.info(f"Cached exchange rates to {self.cache_file}")
        except Exception as e:
            self.logger.warning(f"Failed to cache exchange rates: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cached rates are still valid."""
        if not self.cached_rates:
            return False
        
        cache_age = datetime.now() - self.cached_rates.timestamp
        max_age = timedelta(hours=self.config.cache_duration_hours)
        
        return cache_age < max_age
    
    def _fetch_exchange_rates(self) -> Optional[ExchangeRateData]:
        """Fetch current exchange rates from API."""
        # If requests module is not available, use fallback rates
        if not REQUESTS_AVAILABLE:
            self.logger.warning("Requests module not available, using fallback exchange rates")
            fallback_rates = ExchangeRateData(
                rates=self.config.fallback_multipliers,
                timestamp=datetime.now(),
                source="fallback"
            )
            return fallback_rates
            
        try:
            # Using exchangerate-api.com (free tier allows 1500 requests/month)
            url = f"https://api.exchangerate-api.com/v4/latest/{self.config.base_currency}"
            
            self.logger.info(f"Fetching exchange rates from {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rates_data = ExchangeRateData(
                rates=data['rates'],
                timestamp=datetime.now(),
                source="exchangerate-api.com"
            )
            
            # Cache the new rates
            self._save_cached_rates(rates_data)
            self.cached_rates = rates_data
            
            self.logger.info(f"Successfully fetched exchange rates: {len(rates_data.rates)} currencies")
            return rates_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch exchange rates: {e}")
            return None
    
    def get_exchange_rates(self) -> Dict[str, float]:
        """Get current exchange rates, using cache if valid or fetching new ones."""
        # Check if we have valid cached rates
        if self._is_cache_valid():
            self.logger.info("Using cached exchange rates")
            return self.cached_rates.rates
        
        # Try to fetch new rates
        fresh_rates = self._fetch_exchange_rates()
        if fresh_rates:
            return fresh_rates.rates
        
        # Fall back to cached rates even if expired
        if self.cached_rates:
            self.logger.warning("Using expired cached exchange rates as fallback")
            return self.cached_rates.rates
        
        # Final fallback to hardcoded multipliers
        self.logger.warning("Using hardcoded fallback exchange rates")
        return self.config.fallback_multipliers
    
    def calculate_territorial_price(self, base_price_usd: float, target_currency: str, territory: str = None) -> Dict[str, any]:
        """
        Calculate territorial price with dynamic exchange rates, wiggle room, and market access fees.
        
        Args:
            base_price_usd: Base price in USD
            target_currency: Target currency code (e.g., 'GBP', 'EUR')
            territory: Territory code for specific adjustments
            
        Returns:
            Dict with calculated price, exchange rate used, and breakdown
        """
        try:
            # Get current exchange rates
            exchange_rates = self.get_exchange_rates()
            
            # Get exchange rate for target currency
            if target_currency == self.config.base_currency:
                exchange_rate = 1.0
            else:
                exchange_rate = exchange_rates.get(target_currency)
                if not exchange_rate:
                    # Fallback to hardcoded multiplier
                    exchange_rate = self.config.fallback_multipliers.get(target_currency, 1.0)
                    self.logger.warning(f"Using fallback exchange rate for {target_currency}: {exchange_rate}")
            
            # Convert base price to target currency
            converted_price = base_price_usd * exchange_rate
            
            # Apply wiggle room (extra percentage for unexpected variations)
            # Only apply wiggle room for non-USD currencies
            if target_currency != self.config.base_currency:
                wiggle_room_amount = converted_price * (self.config.wiggle_room_percent / 100)
                price_with_wiggle_room = converted_price + wiggle_room_amount
            else:
                wiggle_room_amount = 0
                price_with_wiggle_room = converted_price
            
            # Apply market access fee (convert USD fee to target currency)
            # Only apply market access fee for non-USD currencies
            if target_currency != self.config.base_currency and self.config.market_access_fee_usd > 0:
                market_access_fee_converted = self.config.market_access_fee_usd * exchange_rate
                final_price = price_with_wiggle_room + market_access_fee_converted
            else:
                market_access_fee_converted = 0
                final_price = price_with_wiggle_room
            
            # Round to 2 decimal places
            final_price = round(final_price, 2)
            
            # Create detailed breakdown
            breakdown = {
                "base_price_usd": base_price_usd,
                "exchange_rate": exchange_rate,
                "converted_price": round(converted_price, 2),
                "wiggle_room_percent": self.config.wiggle_room_percent,
                "wiggle_room_amount": round(wiggle_room_amount, 2),
                "price_with_wiggle_room": round(price_with_wiggle_room, 2),
                "market_access_fee_usd": self.config.market_access_fee_usd,
                "market_access_fee_converted": round(market_access_fee_converted, 2),
                "final_price": final_price,
                "target_currency": target_currency,
                "territory": territory,
                "calculation_timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f"Calculated price for {territory} ({target_currency}): ${base_price_usd} USD -> {final_price} {target_currency}")
            
            return {
                "price": final_price,
                "currency": target_currency,
                "formatted_price": f"{final_price:.2f}",
                "breakdown": breakdown,
                "success": True
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating territorial price: {e}")
            return {
                "price": base_price_usd,
                "currency": self.config.base_currency,
                "formatted_price": f"{base_price_usd:.2f}",
                "breakdown": {"error": str(e)},
                "success": False
            }
    
    def get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol for formatting."""
        symbols = {
            "USD": "$",
            "GBP": "£",
            "EUR": "€",
            "CAD": "C$",
            "AUD": "A$",
            "JPY": "¥",
            "CHF": "CHF",
            "SEK": "kr",
            "NOK": "kr",
            "DKK": "kr"
        }
        return symbols.get(currency_code, currency_code)
    
    def format_price(self, price: float, currency: str) -> str:
        """Format price with appropriate currency symbol."""
        symbol = self.get_currency_symbol(currency)
        if currency == "JPY":
            # Japanese Yen doesn't use decimal places
            return f"{symbol}{int(price)}"
        else:
            return f"{symbol}{price:.2f}"

class MarketSpecificPricingStrategy:
    """Market-specific pricing strategies for different territories."""
    
    def __init__(self, territorial_pricing: TerritorialPricingStrategy):
        self.territorial_pricing = territorial_pricing
        self.logger = logging.getLogger(__name__)
        
        # Market-specific configurations
        self.market_configs = {
            "US": {"currency": "USD", "tax_inclusive": False, "rounding": "standard"},
            "UK": {"currency": "GBP", "tax_inclusive": True, "rounding": "99p"},
            "EU": {"currency": "EUR", "tax_inclusive": True, "rounding": "95c"},
            "CA": {"currency": "CAD", "tax_inclusive": False, "rounding": "standard"},
            "AU": {"currency": "AUD", "tax_inclusive": True, "rounding": "standard"},
            "JP": {"currency": "JPY", "tax_inclusive": True, "rounding": "whole"},
        }
    
    def apply_market_rounding(self, price: float, market: str) -> float:
        """Apply market-specific price rounding strategies."""
        config = self.market_configs.get(market, {"rounding": "99p"})  # Default to 99p rounding
        rounding_strategy = config.get("rounding", "99p")  # Default to 99p rounding
        
        if rounding_strategy == "99p":
            # Round to .99 endings (default style)
            return float(int(price)) + 0.99
        elif rounding_strategy == "95c":
            # Round to .95 endings (EU style)
            return float(int(price)) + 0.95
        elif rounding_strategy == "whole":
            # Round to whole numbers (Japan style)
            return float(int(round(price)))
        elif rounding_strategy == "standard":
            # Standard rounding to 2 decimal places (no special ending)
            return round(price, 2)
        else:
            # Default to .99 rounding for any unknown strategy
            return float(int(price)) + 0.99
    
    def calculate_market_price(self, base_price_usd: float, market: str) -> Dict[str, any]:
        """Calculate price for specific market with market-specific strategies."""
        try:
            market_config = self.market_configs.get(market, self.market_configs["US"])
            currency = market_config["currency"]
            
            # Get base territorial price calculation
            price_result = self.territorial_pricing.calculate_territorial_price(
                base_price_usd, currency, market
            )
            
            if not price_result["success"]:
                return price_result
            
            # Apply market-specific rounding
            rounded_price = self.apply_market_rounding(price_result["price"], market)
            
            # Update result with market-specific adjustments
            price_result.update({
                "price": rounded_price,
                "formatted_price": self.territorial_pricing.format_price(rounded_price, currency),
                "market_config": market_config,
                "rounding_applied": True
            })
            
            # Update breakdown
            price_result["breakdown"]["market_rounded_price"] = rounded_price
            price_result["breakdown"]["rounding_strategy"] = market_config.get("rounding", "standard")
            
            self.logger.info(f"Market-specific price for {market}: {price_result['formatted_price']}")
            
            return price_result
            
        except Exception as e:
            self.logger.error(f"Error calculating market-specific price for {market}: {e}")
            return {
                "price": base_price_usd,
                "currency": "USD",
                "formatted_price": f"${base_price_usd:.2f}",
                "breakdown": {"error": str(e)},
                "success": False
            }