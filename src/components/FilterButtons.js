'use client';

import styles from './FilterButtons.module.css';

const difficultyLevels = [
  { id: 'all', label: 'All', color: '#4a5a7a' },
  { id: 'easy', label: 'Easy', color: '#27ae60' },
  { id: 'medium', label: 'Medium', color: '#f39c12' },
  { id: 'hard', label: 'Hard', color: '#e74c3c' },
];

export default function FilterButtons({ selectedFilter = 'all', onFilterChange }) {
  return (
    <div className={styles.filterContainer}>
      <h3 className={styles.filterTitle}>Filter Tickets</h3>

      <div className={styles.buttonGroup}>
        {difficultyLevels.map((level) => (
          <button
            key={level.id}
            className={`${styles.filterButton} ${
              selectedFilter === level.id ? styles.active : ''
            }`}
            style={{
              backgroundColor: selectedFilter === level.id ? level.color : '#f0f0f0',
              color: selectedFilter === level.id ? '#fff' : '#333',
            }}
            onClick={() => onFilterChange(level.id)}
          >
            {level.label}
          </button>
        ))}
      </div>
    </div>
  );
}