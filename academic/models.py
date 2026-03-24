from django.db import models
from core.models import School
from students.models import Student, Classroom

class Subject(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    # This links subjects to specific classes (e.g., Physics for S.4)
    classrooms = models.ManyToManyField(Classroom, related_name="subjects")

    def __str__(self):
        return f"{self.name} ({self.school.code})"

class Mark(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    term = models.CharField(max_length=20) # '1', '2', or '3'
    year = models.IntegerField(default=2026)
    
    mid_term_mark = models.FloatField(null=True, blank=True)
    end_term_mark = models.FloatField(null=True, blank=True)

    @property
    def total_score(self):
        # Example calculation: 30% Mid, 70% End
        mid = self.mid_term_mark or 0
        end = self.end_term_mark or 0
        return mid + end # Or customize your weighting here

    @property
    def grade(self):
        score = self.total_score
        if score >= 80: return 'D1'
        if score >= 75: return 'D2'
        if score >= 70: return 'C3'
        if score >= 60: return 'C4'
        if score >= 50: return 'P7'
        return 'F9'

    @property
    def grade_remark(self):
        """Returns a standard remark based on the grade."""
        remarks = {
            'D1': 'Excellent', 'D2': 'Very Good',
            'C3': 'Good', 'C4': 'Quite Good', 'C5': 'Satisfactory', 'C6': 'Fair',
            'P7': 'Pass', 'P8': 'Weak Pass', 'F9': 'Fail'
        }
        return remarks.get(self.grade, 'No Grade')

    def __str__(self):
        # Accessing total_score property for the admin display
        return f"{self.student.first_name} - {self.subject.code}: {self.total_score}"