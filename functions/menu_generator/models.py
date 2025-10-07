"""Data models for menu items and nutritional information"""

from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any


@dataclass
class NutritionalInfo:
    """Nutritional information for a menu item"""
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[int] = None
    allergens: List[str] = field(default_factory=list)
    
    @property
    def has_data(self) -> bool:
        """Check if any nutritional data exists"""
        return any([self.calories, self.protein_g, self.carbs_g, self.fat_g])
    
    def format_display(self) -> str:
        """Format for display on calendar"""
        parts = []
        if self.calories:
            parts.append(f"{self.calories} cal")
        if self.protein_g:
            parts.append(f"{self.protein_g}g protein")
        if self.allergens:
            allergen_str = ", ".join(self.allergens[:3])
            parts.append(f"⚠️ {allergen_str}")
        return " | ".join(parts) if parts else "No nutritional info"


@dataclass
class MenuItem:
    """Complete menu item with all metadata"""
    name: str
    day: str
    date: str
    image_path: Optional[str] = None
    nutrition: Optional[NutritionalInfo] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        data = asdict(self)
        if self.nutrition:
            data['nutrition'] = asdict(self.nutrition)
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MenuItem':
        """Create from dictionary"""
        if 'nutrition' in data and data['nutrition']:
            data['nutrition'] = NutritionalInfo(**data['nutrition'])
        return cls(**data)