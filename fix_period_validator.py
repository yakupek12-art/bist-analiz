import os

base_path = r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje"
file_path = os.path.join(base_path, "data_layer.py")

print(f"Using path: {file_path}")
print(f"Exists: {os.path.exists(file_path)}")

with open(file_path, 'rb') as f:
    content = f.read()

# Exact old bytes from the file
old = b'''class PeriodData(BaseModel):
    """Tek bir d\xc3\xb6nem i\xc3\xa7in finansal veriler"""
    period: str
    sales: Optional[float] = None          # Mn TL
    favok: Optional[float] = None          # Mn TL
    net_income: Optional[float] = None     # Mn TL
    favok_margin: Optional[float] = None   # %
    net_margin: Optional[float] = None     # %
    net_debt_favok: Optional[float] = None # x
    current_ratio: Optional[float] = None  # x
    fcf_net_income: Optional[float] = None # %
    roic: Optional[float] = None           # %
    gross_margin: Optional[float] = None   # %
    fcf: Optional[float] = None            # Mn TL
    equity: Optional[float] = None         # Mn TL
    net_debt: Optional[float] = None       # Mn TL
    cash: Optional[float] = None           # Mn TL
    short_debt: Optional[float] = None     # Mn TL
    long_debt: Optional[float] = None      # Mn TL
    total_assets: Optional[float] = None   # Mn TL
    cfo: Optional[float] = None            # Mn TL
    roic_pct: Optional[float] = None       # %
    gross_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    
    @validator('*', pre=True)
    def convert_to_float(cls, v, values, field):
        # Skip period field - it should remain a string
        if field.name == 'period':
            return v
        if v is None or v == '' or v == '-':
            return None
        if isinstance(v, str):
            v = v.replace(',', '').replace('%', '').strip()
            if v == '' or v.lower() in ('nan', 'null', 'none', '-'):
                return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


'''

new = b'''class PeriodData(BaseModel):
    """Tek bir d\xc3\xb6nem i\xc3\xa7in finansal veriler"""
    period: str
    sales: Optional[float] = None          # Mn TL
    favok: Optional[float] = None          # Mn TL
    net_income: Optional[float] = None     # Mn TL
    favok_margin: Optional[float] = None   # %
    net_margin: Optional[float] = None     # %
    net_debt_favok: Optional[float] = None # x
    current_ratio: Optional[float] = None  # x
    fcf_net_income: Optional[float] = None # %
    roic: Optional[float] = None           # %
    gross_margin: Optional[float] = None   # %
    fcf: Optional[float] = None            # Mn TL
    equity: Optional[float] = None         # Mn TL
    net_debt: Optional[float] = None       # Mn TL
    cash: Optional[float] = None           # Mn TL
    short_debt: Optional[float] = None     # Mn TL
    long_debt: Optional[float] = None      # Mn TL
    total_assets: Optional[float] = None   # Mn TL
    cfo: Optional[float] = None            # Mn TL
    roic_pct: Optional[float] = None       # %
    gross_margin_pct: Optional[float] = None
    net_margin_pct: Optional[float] = None
    
    @field_validator('*', mode='before')
    @classmethod
    def convert_to_float(cls, v, info):
        # Skip period field - it should remain a string
        if info.field_name == 'period':
            return v
        if v is None or v == '' or v == '-':
            return None
        if isinstance(v, str):
            v = v.replace(',', '').replace('%', '').strip()
            if v == '' or v.lower() in ('nan', 'null', 'none', '-'):
                return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None


'''

with open(r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\data_layer.py", 'rb') as f:
    content = f.read()

if old in content:
    new_content = content.replace(old, new)
    with open(r"C:\Users\PC\OneDrive\Belgeler\Varsayılan Proje\data_layer.py", 'wb') as f:
        f.write(new_content)
    print('Done!')
else:
    print('Old not found!')
    # Debug: find the actual content
    idx = content.find(b'class PeriodData')
    if idx >= 0:
        print('Found at:', idx)
        print(repr(content[idx:idx+500]))