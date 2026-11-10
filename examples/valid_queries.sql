-- Run the whole file, or copy any query into the Streamlit editor.

SELECT * FROM students;

SELECT department, COUNT(*) FROM employees
WHERE salary >= 50000
GROUP BY department
ORDER BY department ASC;

INSERT INTO students (id, name, score) VALUES
(1, 'Ada Lovelace', 91.5),
(2, 'Lin''s Record', -12);

UPDATE students SET score = score + 5, name = 'Updated Name'
WHERE score IS NOT NULL;

DELETE FROM logs WHERE id = 4 OR level = 'debug';
