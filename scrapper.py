import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from typing import List, Dict
import re

class AnalyticsVidhyaScraper:
    def __init__(self):
        self.base_url = "https://courses.analyticsvidhya.com/pages/all-free-courses"
        self.api_url = "https://courses.analyticsvidhya.com/api/courses"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://courses.analyticsvidhya.com/pages/all-free-courses'
        }

    def fetch_courses(self) -> List[Dict]:
        """Fetch course data from the API"""
        try:
            params = {
                'page': 1,
                'per_page': 100,  # Adjust if needed
                'sort': '-published_at',
                'free': 'true'
            }
            
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            courses = response.json()
            return self._process_courses(courses)
            
        except requests.RequestException as e:
            print(f"Error fetching courses: {e}")
            return []

    def _process_courses(self, courses_data: List[Dict]) -> List[Dict]:
        """Process and clean course data"""
        processed_courses = []
        
        for course in courses_data:
            try:
                # Extract and clean course description
                description = BeautifulSoup(course.get('description', ''), 'html.parser').get_text(strip=True)
                
                processed_course = {
                    'title': course.get('name', '').strip(),
                    'description': description,
                    'instructor': course.get('instructor_name', '').strip(),
                    'url': f"https://courses.analyticsvidhya.com/courses/{course.get('slug', '')}",
                    'image_url': course.get('image_url', ''),
                    'enrollment_count': course.get('enrollment_count', 0),
                    'price': course.get('price', 'Free'),
                    'category': course.get('category', {}).get('name', ''),
                    'duration': self._extract_duration(course.get('description', '')),
                    'level': self._extract_level(description)
                }
                
                processed_courses.append(processed_course)
                
            except Exception as e:
                print(f"Error processing course: {e}")
                continue
                
        return processed_courses

    def _extract_duration(self, description: str) -> str:
        """Extract course duration from description"""
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*mins?',
            r'(\d+)\s*minutes?',
            r'(\d+)\s*weeks?'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Duration not specified"

    def _extract_level(self, description: str) -> str:
        """Extract course level from description"""
        levels = ['Beginner', 'Intermediate', 'Advanced']
        description_lower = description.lower()
        
        for level in levels:
            if level.lower() in description_lower:
                return level
        return "All Levels"

    def save_to_csv(self, courses: List[Dict], filename: str = 'av_courses.csv'):
        """Save courses to CSV file"""
        df = pd.DataFrame(courses)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Saved {len(courses)} courses to {filename}")

    def save_to_json(self, courses: List[Dict], filename: str = 'av_courses.json'):
        """Save courses to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(courses)} courses to {filename}")

def main():
    scraper = AnalyticsVidhyaScraper()
    
    print("Fetching courses from Analytics Vidhya...")
    courses = scraper.fetch_courses()
    
    if courses:
        print(f"\nFound {len(courses)} courses!")
        
        # Save data in both formats
        scraper.save_to_csv(courses)
        scraper.save_to_json(courses)
        
        # Display sample of courses
        print("\nSample of courses found:")
        for course in courses[:3]:
            print(f"\nTitle: {course['title']}")
            print(f"Instructor: {course['instructor']}")
            print(f"Level: {course['level']}")
            print(f"Duration: {course['duration']}")
            print("-" * 50)
    else:
        print("No courses were found. Please check the connection and try again.")

if __name__ == "__main__":
    main()
