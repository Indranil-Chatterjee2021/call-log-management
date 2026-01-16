"""
Extract dropdown values from database
"""

def get_dropdown_values(repo=None):
    """
    Extract dropdown values from database.
    Falls back to empty lists if no data is available.
    
    Args:
        repo: Repository instance (optional, will be retrieved if not provided)
    
    Returns:
        dict: Dictionary of dropdown values for all fields
    """
    if repo is None:
        try:
            from storage import get_repository
            repo = get_repository()
        except:
            # Return empty values if no repository is available
            return _get_empty_dropdowns()
    
    try:
        # Get dropdown values from database
        data = repo.misc_data_get()
        
        if data:
            return {
                'projects': data.get('projects', []),
                'town_types': data.get('town_types', []),
                'requesters': data.get('requesters', []),
                'designations': data.get('designations', []),
                'modules': data.get('modules', []),
                'issues': data.get('issues', []),
                'solutions': data.get('solutions', []),
                'solved_on': data.get('solved_on', []),
                'call_on': data.get('call_on', []),
                'types': data.get('types', [])
            }
        else:
            # No data in database yet
            return _get_empty_dropdowns()
            
    except Exception as e:
        print(f"Error fetching dropdown values from database: {e}")
        return _get_empty_dropdowns()


def _get_empty_dropdowns():
    """Return empty dropdown structure."""
    return {
        'projects': [],
        'town_types': [],
        'requesters': [],
        'designations': [],
        'modules': [],
        'issues': [],
        'solutions': [],
        'solved_on': [],
        'call_on': [],
        'types': []
    }

