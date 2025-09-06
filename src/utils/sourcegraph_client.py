"""
Sourcegraph Client for Code Search and Navigation

This module provides a Python interface to Sourcegraph, replacing the custom MCP
implementation with a more reliable and feature-rich code search solution.
"""

import requests
import json
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class SourcegraphClient:
    """
    Client for interacting with Sourcegraph's GraphQL API.

    This replaces the custom MCP implementation with Sourcegraph's powerful
    code search and navigation capabilities.
    """

    def __init__(self, base_url: str = "http://localhost:7080"):
        """
        Initialize the Sourcegraph client.

        Args:
            base_url: Sourcegraph server URL (default: http://localhost:7080)
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = urljoin(self.base_url, "/.api/graphql")
        self.session = requests.Session()

    def _make_request(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a GraphQL request to Sourcegraph.

        Args:
            query: GraphQL query string
            variables: Optional variables for the query

        Returns:
            Response data from Sourcegraph
        """
        try:
            payload: Dict[str, Any] = {"query": query}
            if variables:
                payload["variables"] = variables

            response = self.session.post(
                self.api_url, json=payload, headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()

            result = response.json()
            if "errors" in result:
                logger.error(f"GraphQL errors: {result['errors']}")
                raise Exception(f"GraphQL errors: {result['errors']}")

            return result.get("data", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise Exception(f"Failed to connect to Sourcegraph: {e}")

    def search_code(
        self,
        query: str,
        repo: Optional[str] = None,
        file_pattern: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict]:
        """
        Search for code using Sourcegraph's search capabilities.

        Args:
            query: Search query (supports semantic and text search)
            repo: Optional repository filter
            file_pattern: Optional file pattern filter (e.g., "*.py")
            limit: Maximum number of results

        Returns:
            List of search results
        """
        # Build search query with filters
        search_query = query
        if repo:
            search_query = f"repo:{repo} {search_query}"
        if file_pattern:
            search_query = f"file:{file_pattern} {search_query}"

        graphql_query = """
        query SearchCode($query: String!, $first: Int!) {
          search(query: $query, version: V2, first: $first) {
            results {
              results {
                file {
                  path
                  name
                  content
                  repository {
                    name
                  }
                }
                symbol {
                  name
                  kind
                  location {
                    resource {
                      path
                    }
                  }
                }
                lineMatches {
                  lineNumber
                  preview
                  offsetAndLengths {
                    start
                    length
                  }
                }
              }
            }
          }
        }
        """

        variables = {"query": search_query, "first": limit}

        result = self._make_request(graphql_query, variables)
        return result.get("search", {}).get("results", {}).get("results", [])

    def find_symbols(self, symbol_name: str, repo: Optional[str] = None) -> List[Dict]:
        """
        Find symbols (functions, classes, variables) in the codebase.

        Args:
            symbol_name: Name of the symbol to search for
            repo: Optional repository filter

        Returns:
            List of symbol definitions
        """
        search_query = f"symbol:{symbol_name}"
        if repo:
            search_query = f"repo:{repo} {search_query}"

        return self.search_code(search_query)

    def find_references(self, symbol_name: str, repo: Optional[str] = None) -> List[Dict]:
        """
        Find all references to a symbol.

        Args:
            symbol_name: Name of the symbol to find references for
            repo: Optional repository filter

        Returns:
            List of symbol references
        """
        search_query = f"refs:{symbol_name}"
        if repo:
            search_query = f"repo:{repo} {search_query}"

        return self.search_code(search_query)

    def get_file_content(self, file_path: str, repo: Optional[str] = None) -> Optional[str]:
        """
        Get the content of a specific file.

        Args:
            file_path: Path to the file
            repo: Optional repository name

        Returns:
            File content as string, or None if not found
        """
        search_query = f"file:{file_path}"
        if repo:
            search_query = f"repo:{repo} {search_query}"

        results = self.search_code(search_query, limit=1)
        if results and results[0].get("file"):
            return results[0]["file"]["content"]
        return None

    def search_by_functionality(self, description: str, repo: Optional[str] = None) -> List[Dict]:
        """
        Search for code by what it does (semantic search).

        Args:
            description: Natural language description of what the code does
            repo: Optional repository filter

        Returns:
            List of relevant code snippets
        """
        # Use semantic search with comment-style query
        search_query = f"// {description}"
        if repo:
            search_query = f"repo:{repo} {search_query}"

        return self.search_code(search_query)

    def get_repository_info(self, repo_name: str) -> Optional[Dict]:
        """
        Get information about a repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Repository information
        """
        graphql_query = """
        query GetRepository($name: String!) {
          repository(name: $name) {
            name
            description
            defaultBranch {
              name
            }
            file(path: "") {
              isDirectory
            }
          }
        }
        """

        variables = {"name": repo_name}
        result = self._make_request(graphql_query, variables)
        return result.get("repository")

    def list_repositories(self) -> List[Dict]:
        """
        List all repositories indexed by Sourcegraph.

        Returns:
            List of repository information
        """
        graphql_query = """
        query ListRepositories($first: Int!) {
          repositories(first: $first) {
            nodes {
              name
              description
              defaultBranch {
                name
              }
            }
          }
        }
        """

        variables = {"first": 100}
        result = self._make_request(graphql_query, variables)
        return result.get("repositories", {}).get("nodes", [])

    def health_check(self) -> bool:
        """
        Check if Sourcegraph is running and accessible.

        Returns:
            True if Sourcegraph is healthy, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/.api/health")
            return response.status_code == 200
        except:
            return False


# Convenience functions for common use cases
def search_job_functions(client: SourcegraphClient, repo: Optional[str] = None) -> List[Dict]:
    """Search for job-related functions in the codebase."""
    return client.search_code("function job", repo=repo, file_pattern="*.py")


def search_scraping_code(client: SourcegraphClient, repo: Optional[str] = None) -> List[Dict]:
    """Search for scraping-related code."""
    return client.search_code("scraper OR scraping", repo=repo, file_pattern="*.py")


def find_database_operations(client: SourcegraphClient, repo: Optional[str] = None) -> List[Dict]:
    """Find database-related operations."""
    return client.search_code("database OR db OR sql", repo=repo, file_pattern="*.py")


def search_dashboard_code(client: SourcegraphClient, repo: Optional[str] = None) -> List[Dict]:
    """Search for dashboard-related code."""
    return client.search_code("dashboard OR flask OR streamlit", repo=repo, file_pattern="*.py")



