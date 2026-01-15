"""
Extract dropdown values from Sheet1
"""
import pandas as pd

def get_dropdown_values():
    """Extract dropdown values from Sheet1"""
    df = pd.read_excel('Verma R Master.xlsx', sheet_name='Sheet1', header=2)
    
    # Extract unique values for each dropdown column
    projects = df['Unnamed: 0'].dropna().unique().tolist()
    projects = [str(p).strip() for p in projects if str(p).strip() and str(p).strip() != 'PROJECT']
    
    town_types = df['Unnamed: 1'].dropna().unique().tolist()
    town_types = [str(t).strip() for t in town_types if str(t).strip() and str(t).strip() != 'TOWN TYPE']
    
    requesters = df['Unnamed: 2'].dropna().unique().tolist()
    requesters = [str(r).strip() for r in requesters if str(r).strip() and str(r).strip() != 'REQUSETER']
    
    designations = df['Unnamed: 7'].dropna().unique().tolist()
    designations = [str(d).strip() for d in designations if str(d).strip() and str(d).strip() != 'DESIGNATION']
    
    modules = df['Unnamed: 9'].dropna().unique().tolist()
    modules = [str(m).strip() for m in modules if str(m).strip() and str(m).strip() != 'MODULE']
    
    issues = df['Unnamed: 10'].dropna().unique().tolist()
    issues = [str(i).strip() for i in issues if str(i).strip() and str(i).strip() != 'ISSUE']
    
    solutions = df['Unnamed: 11'].dropna().unique().tolist()
    solutions = [str(s).strip() for s in solutions if str(s).strip() and str(s).strip() != 'SOLUTION']
    
    solved_on = df['Unnamed: 12'].dropna().unique().tolist()
    solved_on = [str(s).strip() for s in solved_on if str(s).strip() and str(s).strip() != 'SOLVED ON']
    
    call_on = df['Unnamed: 13'].dropna().unique().tolist()
    call_on = [str(c).strip() for c in call_on if str(c).strip() and str(c).strip() != 'CALL ON']
    
    types = df['Unnamed: 14'].dropna().unique().tolist()
    types = [str(t).strip() for t in types if str(t).strip() and str(t).strip() != 'TYPE']
    
    return {
        'projects': sorted([p for p in projects if p]),
        'town_types': sorted([t for t in town_types if t]),
        'requesters': sorted([r for r in requesters if r]),
        'designations': sorted([d for d in designations if d]),
        'modules': sorted([m for m in modules if m]),
        'issues': sorted([i for i in issues if i]),
        'solutions': sorted([s for s in solutions if s]),
        'solved_on': sorted([s for s in solved_on if s]),
        'call_on': sorted([c for c in call_on if c]),
        'types': sorted([t for t in types if t])
    }
