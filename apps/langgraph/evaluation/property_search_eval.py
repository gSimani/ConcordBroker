"""
LangSmith Evaluation Framework for Property Search
Evaluate the quality and accuracy of property search workflows
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from langsmith import Client, wrappers
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)

class PropertySearchEvaluator:
    """Evaluation framework for property search using LangSmith"""
    
    def __init__(self):
        # Initialize LangSmith client
        self.client = Client(
            api_key=os.getenv("LANGSMITH_API_KEY"),
            api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
        )
        
        # Wrap OpenAI for tracing
        self.llm = wrappers.wrap_openai(ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        ))
        
        # Create or get dataset
        self.dataset = self._get_or_create_dataset()
        
    def _get_or_create_dataset(self):
        """Get existing dataset or create new one"""
        dataset_name = "ConcordBroker Property Search"
        
        try:
            # Try to get existing dataset
            datasets = list(self.client.list_datasets())
            for ds in datasets:
                if ds.name == dataset_name:
                    logger.info(f"Using existing dataset: {dataset_name}")
                    return ds
            
            # Create new dataset
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description="Test cases for property search workflow evaluation",
                data_type="kv"
            )
            
            # Add example test cases
            self._add_example_cases(dataset)
            
            logger.info(f"Created new dataset: {dataset_name}")
            return dataset
            
        except Exception as e:
            logger.error(f"Error with dataset: {e}")
            return None
    
    def _add_example_cases(self, dataset):
        """Add example test cases to the dataset"""
        examples = [
            {
                "inputs": {
                    "query": "Find properties in Hollywood under 500000",
                    "filters": {}
                },
                "outputs": {
                    "expected_city": "HOLLYWOOD",
                    "expected_max_value": 500000,
                    "has_results": True,
                    "min_results": 1
                }
            },
            {
                "inputs": {
                    "query": "Show me commercial properties in Fort Lauderdale",
                    "filters": {}
                },
                "outputs": {
                    "expected_city": "FORT LAUDERDALE",
                    "expected_property_type": "commercial",
                    "has_results": True,
                    "min_results": 1
                }
            },
            {
                "inputs": {
                    "query": "Properties owned by Smith in Pompano Beach",
                    "filters": {}
                },
                "outputs": {
                    "expected_city": "POMPANO BEACH",
                    "expected_owner_contains": "SMITH",
                    "has_results": True,
                    "min_results": 0
                }
            },
            {
                "inputs": {
                    "query": "Waterfront properties built after 2000",
                    "filters": {"year_built_min": 2000}
                },
                "outputs": {
                    "expected_year_min": 2000,
                    "has_waterfront": True,
                    "has_results": True,
                    "min_results": 0
                }
            },
            {
                "inputs": {
                    "query": "3930 SW 53 CT Hollywood",
                    "filters": {}
                },
                "outputs": {
                    "expected_address": "3930 SW 53 CT",
                    "expected_city": "HOLLYWOOD",
                    "has_results": True,
                    "exact_match": True,
                    "min_results": 1
                }
            }
        ]
        
        try:
            self.client.create_examples(
                dataset_id=dataset.id,
                examples=examples
            )
            logger.info(f"Added {len(examples)} examples to dataset")
        except Exception as e:
            logger.error(f"Error adding examples: {e}")
    
    def correctness_evaluator(
        self,
        inputs: Dict,
        outputs: Dict,
        reference_outputs: Dict
    ) -> Dict:
        """Evaluate correctness of search results"""
        score = 0.0
        feedback = []
        
        # Check if results were returned when expected
        if reference_outputs.get("has_results"):
            if outputs.get("total", 0) >= reference_outputs.get("min_results", 0):
                score += 0.3
                feedback.append("✓ Found expected results")
            else:
                feedback.append("✗ Insufficient results found")
        
        # Check city extraction
        if reference_outputs.get("expected_city"):
            extracted_city = outputs.get("metadata", {}).get("entities", {}).get("city", "").upper()
            if extracted_city == reference_outputs["expected_city"]:
                score += 0.2
                feedback.append("✓ Correct city identified")
            else:
                feedback.append(f"✗ City mismatch: got {extracted_city}")
        
        # Check value range
        if reference_outputs.get("expected_max_value"):
            extracted_max = outputs.get("metadata", {}).get("entities", {}).get("max_value")
            if extracted_max and extracted_max <= reference_outputs["expected_max_value"]:
                score += 0.2
                feedback.append("✓ Correct value range")
            else:
                feedback.append(f"✗ Value range issue: got {extracted_max}")
        
        # Check owner extraction
        if reference_outputs.get("expected_owner_contains"):
            extracted_owner = outputs.get("metadata", {}).get("entities", {}).get("owner", "").upper()
            if reference_outputs["expected_owner_contains"] in extracted_owner:
                score += 0.2
                feedback.append("✓ Owner correctly identified")
            else:
                feedback.append(f"✗ Owner mismatch: got {extracted_owner}")
        
        # Check property type
        if reference_outputs.get("expected_property_type"):
            extracted_type = outputs.get("metadata", {}).get("entities", {}).get("property_type", "").lower()
            if extracted_type == reference_outputs["expected_property_type"]:
                score += 0.1
                feedback.append("✓ Property type correct")
            else:
                feedback.append(f"✗ Property type mismatch: got {extracted_type}")
        
        return {
            "score": score,
            "feedback": " | ".join(feedback),
            "passed": score >= 0.5
        }
    
    def relevance_evaluator(
        self,
        inputs: Dict,
        outputs: Dict,
        reference_outputs: Dict
    ) -> Dict:
        """Evaluate relevance of search results to query"""
        prompt = f"""
        Evaluate if the search results are relevant to the query.
        
        Query: {inputs.get('query')}
        Number of results: {outputs.get('total', 0)}
        Sample results: {outputs.get('data', {}).get('properties', [])[:3]}
        
        Rate relevance from 0 to 1 where:
        1.0 = Perfectly relevant
        0.5 = Somewhat relevant
        0.0 = Not relevant
        
        Return only the numeric score.
        """
        
        try:
            response = self.llm.invoke(prompt)
            score = float(response.content.strip())
            
            return {
                "score": score,
                "feedback": f"Relevance score: {score:.2f}",
                "passed": score >= 0.5
            }
        except Exception as e:
            logger.error(f"Relevance evaluation error: {e}")
            return {
                "score": 0.0,
                "feedback": "Error evaluating relevance",
                "passed": False
            }
    
    def performance_evaluator(
        self,
        inputs: Dict,
        outputs: Dict,
        reference_outputs: Dict
    ) -> Dict:
        """Evaluate performance metrics"""
        execution_time = outputs.get("execution_time", 999)
        
        # Performance thresholds
        if execution_time < 1.0:
            score = 1.0
            feedback = "Excellent performance"
        elif execution_time < 2.0:
            score = 0.8
            feedback = "Good performance"
        elif execution_time < 5.0:
            score = 0.5
            feedback = "Acceptable performance"
        else:
            score = 0.2
            feedback = "Poor performance"
        
        return {
            "score": score,
            "feedback": f"{feedback} ({execution_time:.2f}s)",
            "passed": score >= 0.5
        }
    
    async def run_evaluation(
        self,
        target_function,
        experiment_name: Optional[str] = None
    ) -> Dict:
        """Run full evaluation suite"""
        
        if not self.dataset:
            logger.error("No dataset available for evaluation")
            return {"error": "Dataset not available"}
        
        experiment_name = experiment_name or f"property_search_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run evaluation
            results = self.client.evaluate(
                target_function,
                data=self.dataset.name,
                evaluators=[
                    self.correctness_evaluator,
                    self.relevance_evaluator,
                    self.performance_evaluator
                ],
                experiment_prefix=experiment_name,
                max_concurrency=2
            )
            
            # Aggregate results
            total_score = 0
            evaluator_scores = {
                "correctness": [],
                "relevance": [],
                "performance": []
            }
            
            for result in results:
                if "correctness" in result:
                    evaluator_scores["correctness"].append(result["correctness"]["score"])
                if "relevance" in result:
                    evaluator_scores["relevance"].append(result["relevance"]["score"])
                if "performance" in result:
                    evaluator_scores["performance"].append(result["performance"]["score"])
            
            # Calculate averages
            avg_scores = {}
            for evaluator, scores in evaluator_scores.items():
                if scores:
                    avg_scores[evaluator] = sum(scores) / len(scores)
                else:
                    avg_scores[evaluator] = 0.0
            
            overall_score = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0.0
            
            logger.info(f"Evaluation complete: {experiment_name}")
            logger.info(f"Overall score: {overall_score:.2f}")
            logger.info(f"Scores by evaluator: {avg_scores}")
            
            return {
                "experiment_name": experiment_name,
                "overall_score": overall_score,
                "evaluator_scores": avg_scores,
                "passed": overall_score >= 0.5,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            return {
                "error": str(e),
                "experiment_name": experiment_name,
                "timestamp": datetime.now().isoformat()
            }
    
    def create_custom_dataset(
        self,
        name: str,
        examples: List[Dict]
    ) -> Optional[Any]:
        """Create a custom dataset for specific evaluation scenarios"""
        try:
            dataset = self.client.create_dataset(
                dataset_name=name,
                description=f"Custom dataset created on {datetime.now()}",
                data_type="kv"
            )
            
            self.client.create_examples(
                dataset_id=dataset.id,
                examples=examples
            )
            
            logger.info(f"Created custom dataset: {name} with {len(examples)} examples")
            return dataset
            
        except Exception as e:
            logger.error(f"Failed to create custom dataset: {e}")
            return None