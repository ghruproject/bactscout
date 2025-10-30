import os
import re

from rich.console import Console

# Initialize Rich console
console = Console()


def extract_sample_name(filename: str) -> str:
    """
    Extract sample name from a FASTQ filename.

    Removes common suffixes like _R1, _1, _R2, _2 and extensions.

    Args:
        filename (str): Path or filename to extract sample name from

    Returns:
        str: Sample name, or empty string if extraction fails

    Examples:
        extract_sample_name("sample_001_R1.fastq.gz") -> "sample_001"
        extract_sample_name("GCA_000001405_1.fq") -> "GCA_000001405"
    """

    # Get just the filename if full path provided
    basename = os.path.basename(filename)

    # Remove extensions (.fastq.gz, .fq.gz, .fastq, .fq)
    name = basename
    for ext in [".fastq.gz", ".fq.gz", ".fastq", ".fq"]:
        if name.endswith(ext):
            name = name[: -len(ext)]
            break

    # Remove read indicators (_R1, _R2, _1, _2)
    patterns = [r"_R[12]$", r"_[12]$"]
    for pattern in patterns:
        name = re.sub(pattern, "", name)

    return name.strip() if name else ""


def print_message(message: str, msg_type: str = "info", emoji: bool = True) -> None:
    """
    Print colored console messages using Rich with different styles for message types.

    Args:
        message: The message text to display
        msg_type: Type of message ('error', 'warning', 'success', 'info', 'debug')
        emoji: Whether to include emoji icons (default: True)

    Examples:
        print_message("Database check passed!", "success")
        print_message("Using default configuration", "warning")
        print_message("Checking system resources...", "info")
    """

    # Define message styles and emojis
    styles = {
        "error": {
            "style": "bold red",
            "emoji": "❌" if emoji else "",
            "prefix": "ERROR",
        },
        "warning": {
            "style": "bold yellow",
            "emoji": "⚠️ " if emoji else "",
            "prefix": "WARNING",
        },
        "success": {
            "style": "bold green",
            "emoji": "✅" if emoji else "",
            "prefix": "SUCCESS",
        },
        "info": {
            "style": "bold blue",
            "emoji": "ℹ️ " if emoji else "",
            "prefix": "INFO",
        },
        "debug": {
            "style": "dim cyan",
            "emoji": "🔍" if emoji else "",
            "prefix": "DEBUG",
        },
    }

    # Get style config or default to info
    config = styles.get(msg_type.lower(), styles["info"])

    # Create formatted message
    emoji_part = f"{config['emoji']} " if config["emoji"] else ""
    prefix_part = f"[{config['style']}]{config['prefix']}[/]"
    message_part = f"[{config['style']}]{message}[/]"

    # Print with Rich
    console.print(f"{emoji_part}{prefix_part}: {message_part}")


def print_header(title: str) -> None:
    """Print a formatted header with Rich styling."""
    console.print(f"\n[bold magenta]{'=' * 60}[/]")
    console.print(f"[bold magenta]{title.center(60)}[/]")
    console.print(f"[bold magenta]{'=' * 60}[/]\n")


def format_summary_headers():
    columns = [
        # Identification
        "sample_id",
        # Overall Status
        "a_final_status",
        # Component Status Flags
        "adapter_detection_status",
        "contamination_status",
        "species_status",
        "coverage_status",
        "coverage_alt_status",
        "duplication_status",
        "filtering_status",
        "gc_content_status",
        "insert_size_status",
        "mlst_status",
        "n_content_status",
        "quality_trend_status",
        "read_length_status",
        "read_q30_status",
        # Species & Contamination
        "species",
        "species_abundance",
        "species_coverage",
        "species_message",
        "contamination_message",
        # Coverage & Duplication
        "coverage_estimate",
        "coverage_message",
        "coverage_alt_estimate",
        "coverage_alt_message",
        "duplication_rate",
        "duplication_message",
        # GC & N-content
        "gc_content",
        "gc_content_lower",
        "gc_content_upper",
        "gc_content_message",
        "n_content_rate",
        "n_content_message",
        # Insert Size & MLST
        "insert_size_peak",
        "insert_size_message",
        "mlst_st",
        "mlst_message",
        # Read Quality & Filtering
        "read1_mean_length",
        "read2_mean_length",
        "read_length_message",
        "read_q20_bases",
        "read_q20_rate",
        "read_q30_bases",
        "read_q30_rate",
        "read_q30_message",
        "read_total_bases",
        "read_total_reads",
        "quality_trend_message",
        "filtering_pass_rate",
        "filtering_message",
        "adapter_detection_message",
        # Reference Genome Info
        "genome_file",
        "genome_file_path",
        "genome_size_expected",
    ]
    return columns
