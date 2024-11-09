import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from typing import List, Dict
import json
from pathlib import Path

class CourseSearchEngine:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.courses = self.load_courses()
        self.course_embeddings = None
        if self.courses:
            self.compute_embeddings()

    def load_courses(self) -> List[Dict]:
        """Load courses from JSON file"""
        try:
            with open('av_courses.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            st.error("Course data not found. Please run the scraper first.")
            return []

    def compute_embeddings(self):
        """Compute embeddings for all courses"""
        texts = [
            f"{course['title']} {course['description']} {course['category']}"
            for course in self.courses
        ]
        self.course_embeddings = self.model.encode(texts, convert_to_tensor=True)

    def semantic_search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search courses using semantic similarity"""
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Calculate cosine similarity
        cos_scores = torch.nn.functional.cosine_similarity(
            query_embedding.unsqueeze(0), self.course_embeddings
        )
        
        # Get top-k matches
        top_results = torch.topk(cos_scores, min(top_k, len(self.courses)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            course = self.courses[idx]
            results.append({
                **course,
                'relevance_score': float(score)
            })
        
        return results

    def filter_courses(self, results: List[Dict], 
                      selected_category: str = None,
                      selected_level: str = None) -> List[Dict]:
        """Filter search results based on category and level"""
        filtered_results = results.copy()
        
        if selected_category and selected_category != "All Categories":
            filtered_results = [
                course for course in filtered_results 
                if course['category'].lower() == selected_category.lower()
            ]
            
        if selected_level and selected_level != "All Levels":
            filtered_results = [
                course for course in filtered_results 
                if course['level'].lower() == selected_level.lower()
            ]
            
        return filtered_results

def create_course_card(course: Dict):
    """Create a visually appealing card for a course"""
    with st.container():
        st.markdown(f"""
        <div style='padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px;'>
            <h3>{course['title']}</h3>
            <p><strong>Relevance Score:</strong> {course.get('relevance_score', 0):.2f}</p>
            <p><strong>Instructor:</strong> {course['instructor']}</p>
            <p><strong>Category:</strong> {course['category']}</p>
            <p><strong>Level:</strong> {course['level']}</p>
            <p><strong>Duration:</strong> {course['duration']}</p>
            <p><strong>Enrolled:</strong> {course['enrollment_count']} students</p>
            <p>{course['description'][:200]}...</p>
            <a href='{course['url']}' target='_blank'>View Course</a>
        </div>
        """, unsafe_allow_html=True)

def main():
    st.set_page_config(page_title="Analytics Vidhya Course Search", layout="wide")
    
    st.title("Analytics Vidhya Course Search")
    st.markdown("""
    Search through Analytics Vidhya's free courses using natural language queries.
    Try searching for specific topics, skills, or technologies!
    """)

    # Initialize search engine
    search_engine = CourseSearchEngine()
    
    if not search_engine.courses:
        st.warning("Please run the scraper first to collect course data.")
        return

    # Sidebar filters
    st.sidebar.title("Filters")
    
    # Get unique categories and levels
    categories = ["All Categories"] + list(set(course['category'] for course in search_engine.courses))
    levels = ["All Levels"] + list(set(course['level'] for course in search_engine.courses))
    
    selected_category = st.sidebar.selectbox("Category", categories)
    selected_level = st.sidebar.selectbox("Level", levels)

    # Main search interface
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input("🔍 Search courses", 
                                   placeholder="e.g., 'machine learning for beginners' or 'python data analysis'")
    
    with col2:
        top_k = st.number_input("Number of results", min_value=1, max_value=20, value=5)

    # Show some statistics
    total_courses = len(search_engine.courses)
    st.markdown(f"Total available courses: **{total_courses}**")

    if search_query:
        # Perform search
        results = search_engine.semantic_search(search_query, top_k=top_k)
        
        # Apply filters
        filtered_results = search_engine.filter_courses(
            results, selected_category, selected_level
        )
        
        if filtered_results:
            st.subheader(f"Found {len(filtered_results)} relevant courses")
            
            # Display results
            for course in filtered_results:
                create_course_card(course)
        else:
            st.info("No courses found matching your criteria. Try adjusting your filters or search query.")

    else:
        # Show featured or random courses when no search query
        st.subheader("Featured Courses")
        featured_courses = sorted(
            search_engine.courses, 
            key=lambda x: x['enrollment_count'], 
            reverse=True
        )[:5]
        
        for course in featured_courses:
            create_course_card(course)

if __name__ == "__main__":
    main()
