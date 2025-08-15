#!/usr/bin/env python3
"""
Find Waterfront Footage Script V4
Enhanced version with additional waterfront/dock features and CSV export for database upload.
"""

import re
import csv
import json
from collections import defaultdict
from typing import List, Dict, Any, Optional
import pandas as pd

# -----------------------
# Utility helpers
# -----------------------
def to_int(x: Optional[str]) -> Optional[int]:
    """Convert string to int, return None if fails"""
    try:
        return int(x)
    except Exception:
        return None

def uniq_join(values: List[str]) -> str:
    """Join unique values with semicolon separator"""
    seen, out = set(), []
    for v in values:
        if not v:
            continue
        key = v.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(v.strip())
    return "; ".join(out)

# -----------------------
# Token & keyword helpers
# -----------------------
WORD = r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*"
FEET_QUOTE = r"['\u2019]"  # straight or curly apostrophe

# Water body / type signals
WATER_TYPES = [
    ("intracoastal", r"\b(?:intracoastal|icw)\b"),
    ("bay",          r"\bbay\b"),
    ("ocean",        r"\bocean\b"),
    ("river",        r"\briver\b"),
    ("canal",        r"\bcanal\b"),
    ("lake",         r"\blake\b"),
    ("gulf",         r"\bgulf\b"),
    ("sound",        r"\bsound\b"),
    ("lagoon",       r"\blagoon\b"),
    ("waterfront",   r"\bwater\s*front(?:age)?\b|\bwaterfront\b|\bwf\b"),
]

# Heuristic keywords that make a snippet "useful"
KEYWORDS = re.compile(
    r"""(?ix)\b(
        water(?:\s*front(?:age)?|frontage|font) |  # waterfront / water front / water-front / waterfont (typo)
        frontage | canal | beach | bay | ocean | intracoastal | icw | river | channel |
        seawall | bulkhead | dock(?:age|s)? | t-?dock | u-?dock |
        slip(?:s)? | boat(?:\s+slip|s)? | lift(?:s)? | moor(?:ing|age)? |
        depth | deep-?water | seawall(?:\s+frontage)? |
        wf
    )\b""",
    re.IGNORECASE
)

STOP_PUNCT = re.compile(r"[.;:!?]")

# -----------------------
# Master patterns
# -----------------------

# 1) Line ID at start
LINE_ID_RE = re.compile(r"(?m)^\s*(\d{9,10})\b(.*)$")

# 2) Core "unit phrase" (2–3 digit number + suffix variations) with context words
UNIT_PHRASE_RE = re.compile(
    rf"""(?ix)
    (?:\b({WORD})\b\s+)?             # [1] two-before (optional)
    (?:\b({WORD})\b\s+)?             # [2] one-before  (optional)
    (?<!\d)(\d{{2,3}})(?!\d)         # [3] the number (2–3 digits)
    (?:                               # suffix variations after the number
        \s*{FEET_QUOTE}(?:\s+(?:slips?|docks?|wf)\b|\b)        # 85' | 85' slip | 85' docks | 85' WF
      | \s*"\s*docks?\b                                   # 90" dock / docks
      | \s*(?:                                            # units / nouns / waterfronty things
            ft\.? | feet | foot | docks? | dockage | slips? |
            water(?:\s*front(?:age)?|frontage|font) | wf |
            frontage | seawall | bulkhead | depth | t-?dock | u-?dock
        )\b
      | \s*(?:ft|ft\.)\s*of\b                             # ft of ...
      | \s*feet\s*of\b                                    # feet of ...
    )
    (?:\s+\b({WORD})\b)?             # [4] one-after  (optional)
    (?:\s+\b({WORD})\b)?             # [5] two-after (optional)
    """,
    re.IGNORECASE | re.VERBOSE
)

# 3) Dimension blocks like 75' x 5'  or 60'×8'
DIMENSION_RE = re.compile(
    rf"""(?ix)
    (?<!\d)(\d{{2,3}})(?!\d)\s*{FEET_QUOTE}\s* [x×] \s*
    (\d{{1,3}})\s*{FEET_QUOTE}
    """,
    re.IGNORECASE | re.VERBOSE
)

# 4) Label forms like "Dock Length: 60", "Water Frontage: 304'"
LABEL_RE = re.compile(
    rf"""(?ix)
    \b(
        (?:dock\s+length) |
        (?:water\s+frontage) |
        (?:seawall) |
        (?:frontage) |
        (?:depth) |
        (?:bridge\s+clearance) |
        (?:canal\s+width)
    )\s*:\s*
    (?:
        (\d{{2,3}})(?!\d)            # [2] plain number
        |
        (\d{{2,4}})\s*{FEET_QUOTE}   # [3] number with trailing quote
    )
    """,
    re.IGNORECASE | re.VERBOSE
)

# 5) Hyphenated adjectives like "70-foot" or "70-foot-wide"
HYPHEN_FOOT_RE = re.compile(
    r"""(?ix)
    (?<!\d)(\d{2,3})(?!\d)\s*-\s*foot(?:\b|-)
    """,
    re.IGNORECASE | re.VERBOSE
)

# 6) Additional patterns from the provided code
RANGE_RE = re.compile(
    rf"""(?ix)
    (?<!\d)(\d{{2,3}})\s*(?:-|–|—|\bto\b)\s*(\d{{2,3}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)
    """
)

SLIP_COUNT_RE = re.compile(r"(?ix)\b(\d{1,2})\s+(?:boat\s+)?slips?\b")
MAX_LENGTH_RE = re.compile(rf"(?ix)(?:up\s*to|accommodate(?:s|d)?|fits?|for)\s+(\d{{2,3}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)\s*(?:boat|vessel|yacht)?")
MAX_BEAM_RE = re.compile(rf"(?ix)\bbeam\s*(?:of|up\s*to|:)?\s*(\d{{1,2}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)\b")
LIFT_K_RE = re.compile(r"(?ix)\b(\d{2,3})\s*k\s*(?:lb|pounds?)\b")
LIFT_LB_RE = re.compile(r"(?ix)\b(\d{4,6})\s*(?:lb|pounds?)\b.*\blift\b")
DEPTH_RE = re.compile(rf"(?ix)\b(\d{{1,2}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)\s*(?:at\s*)?(?:mlw|mean\s+low\s+water|low\s+tide)\b")
NO_FIXED_BRIDGES_RE = re.compile(r"(?ix)\bno\b.{0,6}\bfixed\s+bridges?\b")
BRIDGE_CLEARANCE_RE = re.compile(rf"(?ix)\b(\d{{2,3}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)\s*(?:bridge\s+clearance|clearance)\b")
DIST_TO_INLET_RE = re.compile(r"(?ix)\b(\d{1,2})\s*(?:min|minutes?)\s*(?:to|to\s+the)\s*(?:inlet|ocean)\b")
CANAL_WIDTH_RE = re.compile(rf"(?ix)\b(\d{{2,3}})\s*(?:{FEET_QUOTE}\b|ft\.?\b|feet\b)\s*(?:canal\s+width|wide\s+canal|canal\s+wide)\b")

# -----------------------
# Utilities
# -----------------------

def expand_useful_context(rest: str, start: int, end: int, min_tokens_after: int = 5, max_chars: int = 160) -> str:
    """
    Expand [start:end] to include more context when needed.
    - Ensure at least `min_tokens_after` tokens after the match (unless punctuation)
    - Stop expansion at sentence punctuation or max_chars.
    - If the expanded snippet still lacks KEYWORDS, extend a bit more (once).
    """
    snippet = rest[start:end]

    # Try extend forward to punctuation or token count
    forward = rest[end:]
    # stop at first strong punctuation
    m = STOP_PUNCT.search(forward)
    forward_limit = m.start() if m else len(forward)

    # make sure we have enough tokens after
    after_tokens = re.findall(rf"{WORD}", forward[:forward_limit], flags=re.IGNORECASE)
    extra_span = forward_limit
    if len(after_tokens) < min_tokens_after:
        # allow more until we hit next punctuation
        extra_span = min(len(forward), forward_limit + 80)

    extended = (rest[max(0, start-40):start] + snippet + forward[:extra_span]).strip()
    extended = extended[:max_chars].strip()

    # If still not useful (no waterfront/dock/etc), try one more light extension
    if not KEYWORDS.search(extended):
        more = forward[extra_span:extra_span+120]
        extended = (extended + " " + more).strip()[:max_chars].strip()

    return extended

def categorize_measurement(snippet: str, expanded: str, match_type: str, label: str = None) -> Dict[str, Any]:
    """
    Categorize the measurement into specific fields when possible.
    Returns a dict with categorized measurements and confidence levels.
    """
    s = (snippet + " " + expanded).lower()
    label_lower = label.lower() if label else ""
    
    # Initialize measurement fields
    measurements = {
        'dock_length': None,
        'waterfront_length': None,
        'seawall_length': None,
        'slip_length': None,
        'depth': None,
        'other_length': None
    }
    
    # Extract the number from the snippet
    number_match = re.search(r'(\d{2,3})', snippet)
    if not number_match:
        return measurements
    
    number = int(number_match.group(1))
    
    # High confidence categorizations based on explicit labels
    if match_type == "label":
        if "dock length" in label_lower:
            measurements['dock_length'] = number
            return measurements
        elif "water frontage" in label_lower:
            measurements['waterfront_length'] = number
            return measurements
        elif "seawall" in label_lower:
            measurements['seawall_length'] = number
            return measurements
        elif "depth" in label_lower:
            measurements['depth'] = number
            return measurements
        elif "frontage" in label_lower:
            measurements['waterfront_length'] = number
            return measurements
    
    # Medium confidence categorizations based on context
    if match_type == "dimension":
        try:
            # For dimensions like "25'x135'" or "25'×135'", extract the numbers
            # Handle both regular 'x' and multiplication '×' symbols
            if 'x' in snippet or '×' in snippet:
                # Split on either x or × and clean up the numbers
                parts = re.split(r'[x×]', snippet)
                if len(parts) == 2:
                    # Extract numbers, removing any non-digit characters
                    width_str = re.sub(r'[^\d]', '', parts[0].strip())
                    height_str = re.sub(r'[^\d]', '', parts[1].strip())
                    
                    if width_str and height_str:
                        width, height = int(width_str), int(height_str)
                        if width > height:
                            measurements['waterfront_length'] = width
                            measurements['other_length'] = height
                        else:
                            measurements['waterfront_length'] = height
                            measurements['other_length'] = width
        except (ValueError, IndexError):
            # If dimension parsing fails, fall back to context-based categorization
            pass
    
    # Context-based categorization
    if re.search(r'\bdock(?:age|s?)\b|\bt-?dock\b|\bu-?dock\b', s):
        measurements['dock_length'] = number
    elif re.search(r'\bseawall\b|\bbulkhead\b', s):
        measurements['seawall_length'] = number
    elif re.search(r'\bslips?\b|\bboat\s+slips?\b', s):
        measurements['slip_length'] = number
    elif re.search(r'\bwater(?:\s*front(?:age)?|frontage|font)\b|\bwf\b|\bfrontage\b', s):
        measurements['waterfront_length'] = number
    elif re.search(r'\bdepth\b', s):
        measurements['depth'] = number
    elif re.search(r'\bft\.?\b|\bfeet\b|\bfoot\b|'+FEET_QUOTE, s):
        # If we can't determine specific type, put in other_length
        measurements['other_length'] = number
    
    return measurements

def extract_from_line(line_id: str, rest: str) -> Dict[str, Any]:
    """Extract all waterfront features from a single line"""
    feats: Dict[str, Any] = defaultdict(list)
    snippets: List[str] = []
    
    # Waterfront types (normalize to a small set)
    wtypes = []
    for name, pat in WATER_TYPES:
        if re.search(pat, rest, flags=re.IGNORECASE):
            wtypes.append(name)
    if wtypes:
        feats["waterfront_type"].append(uniq_join(wtypes))

    # Unit phrases
    for m in UNIT_PHRASE_RE.finditer(rest):
        start, end = m.span()
        snippet = rest[start:end].strip()
        expanded = expand_useful_context(rest, start, end)
        snippets.append(snippet)
        
        val = to_int(m.group(3))
        s = snippet.lower()
        if val is None:
            continue
        if re.search(r"\b(waterfront|water\s*front|frontage|wf|seawall|bulkhead)\b", s):
            feats["waterfront_linear_ft"].append(val)
        if re.search(r"\b(dock|dockage|t-?dock|u-?dock|slip|slips)\b", s):
            feats["dock_linear_ft"].append(val)
        if re.search(r"\bdepth\b", s):
            feats["depth_at_mlw_ft"].append(val)

    # Labeled forms
    for m in LABEL_RE.finditer(rest):
        label = m.group(1).lower()
        number = to_int(m.group(2) or m.group(3))
        snippet = rest[m.start():m.end()]
        snippets.append(snippet)
        if number is None:
            continue
        if "water frontage" in label or label == "frontage":
            feats["waterfront_linear_ft"].append(number)
        elif "dock length" in label:
            feats["dock_linear_ft"].append(number)
        elif "seawall" in label:
            feats["waterfront_linear_ft"].append(number)
        elif "depth" in label:
            feats["depth_at_mlw_ft"].append(number)
        elif "bridge clearance" in label:
            feats["bridge_clearance_ft"].append(number)
        elif "canal width" in label:
            feats["canal_width_ft"].append(number)

    # Ranges -> estimate (mean) and assign based on nearby words
    for m in RANGE_RE.finditer(rest):
        a, b = to_int(m.group(1)), to_int(m.group(2))
        if a and b:
            est = int(round((a + b) / 2))
            around = rest[max(0, m.start()-40):m.end()+40].lower()
            if re.search(r"\b(waterfront|water\s*front|frontage|wf|seawall|bulkhead)\b", around):
                feats["waterfront_linear_ft"].append(est)
            if re.search(r"\b(dock|dockage|t-?dock|u-?dock|slip|slips)\b", around):
                feats["dock_linear_ft"].append(est)
            snippets.append(rest[m.start():m.end()])

    # Slip count, vessel size, beam
    for m in SLIP_COUNT_RE.finditer(rest):
        feats["slip_count"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])
    for m in MAX_LENGTH_RE.finditer(rest):
        feats["max_vessel_length_ft"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])
    for m in MAX_BEAM_RE.finditer(rest):
        feats["max_vessel_beam_ft"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])

    # Lift capacity
    for m in LIFT_K_RE.finditer(rest):
        k = to_int(m.group(1))
        if k:
            feats["lift_capacity_lbs"].append(k * 1000)
            snippets.append(rest[m.start():m.end()])
    for m in LIFT_LB_RE.finditer(rest):
        lbs = to_int(m.group(1))
        if lbs:
            feats["lift_capacity_lbs"].append(lbs)
            snippets.append(rest[m.start():m.end()])

    # Depth at MLW / low tide
    for m in DEPTH_RE.finditer(rest):
        feats["depth_at_mlw_ft"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])

    # Bridges / inlet distance / canal width
    if NO_FIXED_BRIDGES_RE.search(rest):
        feats["no_fixed_bridges"].append(True)
        snippets.append("no fixed bridges")
    for m in BRIDGE_CLEARANCE_RE.finditer(rest):
        feats["bridge_clearance_ft"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])
    for m in DIST_TO_INLET_RE.finditer(rest):
        feats["distance_to_inlet_minutes"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])
    for m in CANAL_WIDTH_RE.finditer(rest):
        feats["canal_width_ft"].append(to_int(m.group(1)))
        snippets.append(rest[m.start():m.end()])

    # Choose a representative snippet (prioritize strong waterfront/dock indicators)
    snippet = ""
    if snippets:
        strong = [s for s in snippets if re.search(r"\b(waterfront|frontage|dock|dockage|slip|seawall|wf|depth|bridge|canal)\b", s, flags=re.IGNORECASE)]
        snippet = (strong[0] if strong else snippets[0])[:240]

    # Flatten to a single row with all our enhanced fields
    row = {
        "line_id": line_id,
        "snippet": snippet,
        "waterfront_linear_ft": max([v for v in feats.get("waterfront_linear_ft", []) if v is not None], default=None),
        "dock_linear_ft": max([v for v in feats.get("dock_linear_ft", []) if v is not None], default=None),
        "slip_count": max([v for v in feats.get("slip_count", []) if v is not None], default=None),
        "max_vessel_length_ft": max([v for v in feats.get("max_vessel_length_ft", []) if v is not None], default=None),
        "max_vessel_beam_ft": max([v for v in feats.get("max_vessel_beam_ft", []) if v is not None], default=None),
        "lift_capacity_lbs": max([v for v in feats.get("lift_capacity_lbs", []) if v is not None], default=None),
        "depth_at_mlw_ft": max([v for v in feats.get("depth_at_mlw_ft", []) if v is not None], default=None),
        "no_fixed_bridges": True if True in feats.get("no_fixed_bridges", []) else False,
        "bridge_clearance_ft": max([v for v in feats.get("bridge_clearance_ft", []) if v is not None], default=None),
        "distance_to_inlet_minutes": max([v for v in feats.get("distance_to_inlet_minutes", []) if v is not None], default=None),
        "canal_width_ft": max([v for v in feats.get("canal_width_ft", []) if v is not None], default=None),
        "waterfront_type": uniq_join(feats.get("waterfront_type", [])),
        # Additional fields from our categorization
        "dock_length": max([v for v in feats.get("dock_linear_ft", []) if v is not None], default=None),
        "waterfront_length": max([v for v in feats.get("waterfront_linear_ft", []) if v is not None], default=None),
        "seawall_length": None,  # Will be populated from our detailed analysis
        "slip_length": None,     # Will be populated from our detailed analysis
        "depth": max([v for v in feats.get("depth_at_mlw_ft", []) if v is not None], default=None),
        "other_length": None,    # Will be populated from our detailed analysis
    }
    
    return row

def extract_matches(text: str) -> List[Dict[str, Any]]:
    """
    Parse the whole document; return a list of matches across all lines.
    Each dict includes line_id and all extracted waterfront features.
    """
    all_matches: List[Dict[str, Any]] = []
    for m in LINE_ID_RE.finditer(text):
        line_id, rest = m.group(1), m.group(2)
        all_matches.append(extract_from_line(line_id, rest))
    return all_matches

class WaterfrontFootageFinderV4:
    def __init__(self, export_file: str):
        self.export_file = export_file
        self.results = []
        self.summary = {}
    
    def load_export_file(self) -> str:
        """Load the exported listings data file"""
        try:
            with open(self.export_file, 'r', encoding='utf-8') as f:
                content = f.read()
            print(f"✅ Loaded export file: {self.export_file}")
            print(f"📊 File size: {len(content):,} characters")
            return content
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return ""
    
    def find_footage(self) -> List[Dict[str, Any]]:
        """Find waterfront footage using the enhanced extractor"""
        print("🔍 Searching for waterfront footage patterns with enhanced features...")
        
        content = self.load_export_file()
        if not content:
            return []
        
        # Extract matches using the enhanced extractor
        self.results = extract_matches(content)
        
        print(f"✅ Found {len(self.results)} waterfront property records")
        return self.results
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze the extracted waterfront features"""
        if not self.results:
            print("❌ No results to analyze. Run find_footage() first.")
            return {}
        
        print("📊 Analyzing extracted waterfront features...")
        
        analysis = {
            'total_properties': len(self.results),
            'properties_with_waterfront': len([r for r in self.results if r['waterfront_linear_ft']]),
            'properties_with_docks': len([r for r in self.results if r['dock_linear_ft']]),
            'properties_with_slips': len([r for r in self.results if r['slip_count']]),
            'properties_with_lifts': len([r for r in self.results if r['lift_capacity_lbs']]),
            'properties_with_depth': len([r for r in self.results if r['depth_at_mlw_ft']]),
            'properties_no_fixed_bridges': len([r for r in self.results if r['no_fixed_bridges']]),
            'waterfront_types': defaultdict(int),
            'sample_properties': []
        }
        
        # Analyze each property
        for result in self.results:
            # Track waterfront types
            if result['waterfront_type']:
                analysis['waterfront_types'][result['waterfront_type']] += 1
            
            # Add to sample properties (first 20)
            if len(analysis['sample_properties']) < 20:
                analysis['sample_properties'].append({
                    'zpid': result['line_id'],
                    'snippet': result['snippet'],
                    'waterfront_ft': result['waterfront_linear_ft'],
                    'dock_ft': result['dock_linear_ft'],
                    'slip_count': result['slip_count'],
                    'waterfront_type': result['waterfront_type']
                })
        
        self.summary = analysis
        return analysis
    
    def show_results(self):
        """Display the analysis results"""
        if not self.summary:
            print("❌ No analysis results to show. Run analyze_results() first.")
            return
        
        print("\n🌊 WATERFRONT FEATURES ANALYSIS RESULTS V4")
        print("=" * 70)
        print(f"Total Properties Analyzed: {self.summary['total_properties']}")
        print(f"Properties with Waterfront: {self.summary['properties_with_waterfront']}")
        print(f"Properties with Docks: {self.summary['properties_with_docks']}")
        print(f"Properties with Slips: {self.summary['properties_with_slips']}")
        print(f"Properties with Lifts: {self.summary['properties_with_lifts']}")
        print(f"Properties with Depth Info: {self.summary['properties_with_depth']}")
        print(f"Properties with No Fixed Bridges: {self.summary['properties_no_fixed_bridges']}")
        
        print(f"\n🏷️  Waterfront Types Found:")
        for wtype, count in sorted(self.summary['waterfront_types'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {wtype}: {count} properties")
        
        print(f"\n📋 Sample Properties (first 20):")
        for i, prop in enumerate(self.summary['sample_properties'], 1):
            print(f"  {i:2d}. ZPID {prop['zpid']}")
            print(f"       Snippet: {prop['snippet']}")
            print(f"       Waterfront: {prop['waterfront_ft']} ft | Dock: {prop['dock_ft']} ft | Slips: {prop['slip_count']}")
            print(f"       Type: {prop['waterfront_type']}")
            print()
    
    def save_results(self, output_file: str = None):
        """Save the results to JSON and CSV files"""
        if not self.results:
            print("❌ No results to save. Run find_footage() first.")
            return
        
        # Save JSON
        json_file = output_file.replace('.csv', '.json') if output_file else f"waterfront_features_v4_{len(self.results)}_properties.json"
        try:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'summary': self.summary,
                    'detailed_results': self.results
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ JSON results saved to: {json_file}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")
        
        # Save CSV
        csv_file = output_file or f"waterfront_features_v4_{len(self.results)}_properties.csv"
        try:
            df = pd.DataFrame(self.results)
            df.to_csv(csv_file, index=False)
            print(f"✅ CSV results saved to: {csv_file}")
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
    
    def run_analysis(self):
        """Run the complete waterfront features analysis"""
        print("🚀 Starting Waterfront Features Analysis V4...")
        print(f"📁 Using export file: {self.export_file}")
        
        # Find footage
        self.find_footage()
        
        # Analyze results
        self.analyze_results()
        
        # Show results
        self.show_results()
        
        # Save results
        self.save_results()
        
        print("\n✅ Analysis complete!")

def main():
    """Main function"""
    # Use the most recent export file
    import glob
    export_files = glob.glob("listings_data_export_v2_*.txt")
    
    if not export_files:
        print("❌ No export files found. Please run the export script first.")
        return
    
    # Use the most recent file
    latest_export = sorted(export_files)[-1]
    print(f"📁 Using latest export file: {latest_export}")
    
    # Run analysis
    finder = WaterfrontFootageFinderV4(latest_export)
    finder.run_analysis()

if __name__ == "__main__":
    main()


