# styles.py

SEGMENTED_CONTROL_CSS = """
<style>
.segmented-control {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}
.segmented-control button {
  border: 2px solid #ccc;
  border-radius: 999px;
  padding: 0.4rem 1rem;
  background-color: transparent;
  color: #333;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}
.segmented-control button.active {
  color: white;
}
.segmented-control button[data-value="Y"].active {
  background-color: #4CAF50;
  border-color: #4CAF50;
}
.segmented-control button[data-value="N"].active {
  background-color: #F44336;
  border-color: #F44336;
}
.segmented-control button[data-value="M"].active {
  background-color: #FFEB3B;
  border-color: #FFEB3B;
  color: #333;
}
.segmented-control button[data-value="NR"].active {
  background-color: #2196F3;
  border-color: #2196F3;
}
@media (max-width: 768px) {
  .segmented-control {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
"""
