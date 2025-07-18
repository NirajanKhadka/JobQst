#!/usr/bin/env python3
"""
Document Quality Validation Script
Validates generated documents for placeholder text and quality issues.
"""

import os
from pathlib import Path
from typing import List, Dict
from rich.console import Console
from rich.table import Table

console = Console()

def validate_document_quality(file_path: Path) -> Dict[str, any]:
    """
    Validate a document for common quality issues.
    
    Args:
        file_path: Path to the document file
        
    Returns:
        Dictionary with validation results
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return {"error": f"Could not read file: {e}", "valid": False}
    
    issues = []
    placeholders_found = []
    
    # Common placeholder patterns to detect
    placeholder_patterns = [
        '[Your Name]', '[Your Address]', '[City, State', '[Zip Code]',
        '[University Name]', '[Degree]', '[Field of Study]', '[Year of Graduation]',
        '[Company Name]', '[Recipient\'s Name]', '[Today\'s Date]',
        '[Email:', '[Phone:', '[Position]', '[Organization]',
        '*(Your Entry Level Experience', '*(List any notable projects',
        '[link]', '[Link to', '[GitHub repository]'
    ]
    
    # Check for placeholder text
    for pattern in placeholder_patterns:
        if pattern in content:
            placeholders_found.append(pattern)
    
    # Check document length (should be substantial)
    word_count = len(content.split())
    if word_count < 100:
        issues.append(f"Document too short ({word_count} words)")
    
    # Check if actual profile information is used
    required_elements = ['Nirajan Khadka', 'Mississauga', 'Nirajan.Tech@gmail.com']
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    return {
        "valid": len(placeholders_found) == 0 and len(issues) == 0,
        "placeholders": placeholders_found,
        "issues": issues,
        "missing_elements": missing_elements,
        "word_count": word_count,
        "file_size": len(content)
    }

def validate_profile_documents(profile_name: str = "Nirajan") -> None:
    """
    Validate all generated documents for a profile.
    
    Args:
        profile_name: Name of the profile to validate
    """
    console.print(f"\n🔍 [bold blue]Validating documents for profile: {profile_name}[/bold blue]")
    
    profile_dir = Path(f"profiles/{profile_name}/generated_documents")
    if not profile_dir.exists():
        console.print(f"❌ [red]Generated documents directory not found: {profile_dir}[/red]")
        return
    
    # Get all text files in the directory
    document_files = list(profile_dir.glob("*.txt"))
    if not document_files:
        console.print(f"❌ [red]No documents found in: {profile_dir}[/red]")
        return
    
    # Validation results table
    table = Table(title="Document Validation Results")
    table.add_column("Document", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Word Count", justify="right")
    table.add_column("Issues", style="yellow")
    
    all_valid = True
    
    for doc_file in sorted(document_files):
        console.print(f"📄 Validating: {doc_file.name}")
        
        validation = validate_document_quality(doc_file)
        
        if validation.get("error"):
            table.add_row(
                doc_file.name,
                "❌ ERROR",
                "N/A", 
                validation["error"]
            )
            all_valid = False
            continue
        
        status = "✅ VALID" if validation["valid"] else "❌ INVALID"
        if not validation["valid"]:
            all_valid = False
        
        # Compile issues list
        all_issues = []
        if validation["placeholders"]:
            all_issues.append(f"Placeholders: {', '.join(validation['placeholders'])}")
        if validation["issues"]:
            all_issues.extend(validation["issues"])
        if validation["missing_elements"]:
            all_issues.append(f"Missing: {', '.join(validation['missing_elements'])}")
        
        issues_text = "; ".join(all_issues) if all_issues else "None"
        
        table.add_row(
            doc_file.name,
            status,
            str(validation["word_count"]),
            issues_text
        )
    
    console.print(table)
    
    # Summary
    if all_valid:
        console.print("\n🎉 [bold green]ALL DOCUMENTS PASSED VALIDATION![/bold green]")
        console.print("✅ No placeholder text detected")
        console.print("✅ All documents contain proper personal information")
        console.print("✅ Documents are ready for professional use")
    else:
        console.print("\n⚠️ [bold yellow]SOME DOCUMENTS HAVE ISSUES[/bold yellow]")
        console.print("🔧 Consider regenerating documents with issues")
        console.print("📋 Check the issues column for specific problems")

def main():
    """Main function to run document validation."""
    console.print("[bold]🔍 AutoJobAgent Document Quality Validator[/bold]")
    console.print("This tool validates generated resumes and cover letters for quality issues.\n")
    
    # Validate Nirajan profile documents
    validate_profile_documents("Nirajan")
    
    console.print(f"\n📊 [cyan]Validation complete![/cyan]")
    console.print("💡 [dim]Run this script after generating documents to ensure quality.[/dim]")

if __name__ == "__main__":
    main()
