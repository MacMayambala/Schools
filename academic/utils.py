from django.db.models import Sum, Avg
from .models import Mark

def get_class_ranking(classroom, term, year):
    """
    Returns a dictionary of student IDs and their rank (1st, 2nd, etc.)
    based on their average score across all subjects.
    """
    rankings = Mark.objects.filter(
        classroom=classroom, 
        term=term, 
        year=year
    ).values('student').annotate(
        avg_score=Avg('end_term_mark') # You can change this to a weighted formula
    ).order_by('-avg_score')

    ranked_dict = {}
    for index, entry in enumerate(rankings):
        ranked_dict[entry['student']] = index + 1
    return ranked_dict