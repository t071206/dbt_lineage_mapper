# DBT Lineage Mapper

A tool for creating lineage mappings between multiple dbt projects. This tool can analyze dbt projects from both GitHub repositories and local file systems, extracting dependencies between models and generating visualizations in various formats.

## Features

- Support for both GitHub repositories and local file systems
- Parsing of dbt_project.yml and schema.yml files
- Extraction of model dependencies from SQL files
- Cross-project reference detection with dual resolution methods:
  - Profiles.yml integration for accurate cross-project lineage based on compiled table names
  - Name-based inference as a fallback mechanism
- Multiple output formats:
  - Mermaid diagram for visualization in Markdown
  - Interactive HTML visualization with Cytoscape.js
  - JSON for programmatic access
  - CSV for data analysis in spreadsheets or BI tools
- Compiled BigQuery table name extraction

## Requirements

- Python 3.6+
- Required Python packages:
  - PyYAML
  - requests

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd dbt-lineage
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

1. Create a file named `repo_list.txt` containing the list of repositories to analyze, one per line. These can be either GitHub repository URLs or local file paths:

   ```
   https://github.com/organization/dbt-project-1
   https://github.com/organization/dbt-project-2
   C:\path\to\local\dbt-project-3
   ```

2. Run the tool:
   ```
   python main.py
   ```

3. By default, the tool will generate an interactive HTML visualization in `output/lineage.html` that shows the lineage between models across all projects. A web server will automatically start and open the visualization in your default web browser.

4. You can also generate output in other formats:
   ```
   python main.py --format json  # Generates lineage.json
   python main.py --format csv   # Generates lineage_nodes.csv and lineage_edges.csv
   ```

5. To display the lineage for a specific model:
   ```
   python main.py --select cpo_po_core  # Shows lineage for cpo_po_core model
   python main.py --select cpo_po_core --depth 2  # Shows lineage with max depth of 2
   ```

### Command Line Options

```
python main.py --help
```

Available options:

- `--repo-list`: Path to file containing list of repositories (default: `repo_list.txt`)
- `--output`: Path to output file without extension (default: `lineage`)
- `--format`: Output format - html, json, or csv (default: `html`)
- `--select`: Select a specific model to display its lineage (e.g., `--select cpo_po_core`)
- `--depth`: Maximum depth for model lineage traversal (default: unlimited)
- `--github-token`: GitHub API token for authentication (can also be set via GITHUB_TOKEN env var)
- `--no-server`: Do not start a web server for HTML output (by default, a server is started)
- `--port`: Port to use for the web server (default: 8000)
- `--verbose`: Enable verbose logging

### Environment Variables

The application uses environment variables for configuration. You can set these in a `.env` file in the project root (recommended) or directly in your environment.

A `.env.example` file is provided as a template. Simply copy it to `.env` and add your values:
```
cp .env.example .env
# Then edit .env with your values
```

#### Available Environment Variables

1. **GITHUB_TOKEN**: GitHub API token for authentication with GitHub repositories
   ```
   # .env file
   GITHUB_TOKEN=your_github_token
   ```

2. **PORT**: Port to use for the web server (default: 8000)
   ```
   # .env file
   PORT=8000
   ```

3. **DBT_PROFILES_PATH**: Path to the dbt profiles.yml file
   ```
   # .env file
   DBT_PROFILES_PATH=~/.dbt/profiles.yml
   ```
   This setting allows the tool to read your dbt profiles.yml file to determine the actual compiled table names for more accurate cross-project lineage. The default path is `~/.dbt/profiles.yml`.

4. **DBT_PROFILE_TARGET**: Target environment to use from profiles.yml
   ```
   # .env file
   DBT_PROFILE_TARGET=dev
   ```
   This setting specifies which target environment from your profiles.yml to use for compiled table names. If the specified target is not found, the tool will fall back to the default target defined in your profiles.yml.

5. **HTTP_PROXY** and **HTTPS_PROXY**: Proxy settings for GitHub API requests
   ```
   # .env file
   # Format: protocol://username:password@host:port
   HTTP_PROXY=http://user:pass@proxy.example.com:8080
   HTTPS_PROXY=https://user:pass@proxy.example.com:8443
   ```
   These settings are useful when you need to access GitHub from within a VPN or corporate network that requires a proxy. Leave them empty if you don't need a proxy.

### GitHub Authentication

For private GitHub repositories, you'll need to provide a GitHub API token. You can do this in three ways:

1. Set it in your `.env` file (recommended):
   ```
   # .env file
   GITHUB_TOKEN=your_github_token
   ```

2. Set the `GITHUB_TOKEN` environment variable:
   ```
   export GITHUB_TOKEN=your_github_token
   ```

3. Pass the token as a command line argument:
   ```
   python main.py --github-token your_github_token
   ```

Note: The `.env` file is included in `.gitignore` to prevent accidentally committing your token to version control.

#### How to Get a GitHub Token

To create a GitHub Personal Access Token (PAT):

1. Log in to your GitHub account
2. Click on your profile picture in the top-right corner and select "Settings"
3. Scroll down to the bottom of the sidebar and click on "Developer settings"
4. Click on "Personal access tokens" and then "Tokens (classic)"
5. Click "Generate new token" and then "Generate new token (classic)"
6. Give your token a descriptive name in the "Note" field
7. Select the scopes (permissions) needed:
   - For public repositories: select `repo:status` and `public_repo`
   - For private repositories: select the entire `repo` scope
8. Click "Generate token"
9. Copy the token immediately (you won't be able to see it again!)
10. Paste it into your `.env` file as shown above

Remember that tokens are like passwords - keep them secure and never commit them to version control.

## Output Formats

### Interactive HTML Visualization (Default)

The HTML output format provides an interactive web-based visualization of the lineage graph. This is similar to the visualization provided by dbt's documentation site, allowing you to explore the relationships between models interactively.

Example command:
```
python main.py --format html --output lineage
```

This will generate `lineage.html` with an interactive visualization that includes:
- Interactive graph with nodes and edges
- Ability to zoom, pan, and fit the graph
- Search functionality to find specific nodes
- Node details sidebar that shows when clicking on a node
- Upstream and downstream dependency lists
- Color-coded nodes for different types (models, sources)
- Highlighted cross-project references

By default, the tool will automatically start a web server and open the visualization in your default web browser. The server will continue running until you press Ctrl+C in the terminal.

If you don't want to start a web server, you can use the `--no-server` option:
```
python main.py --format html --output lineage --no-server
```

You can specify a custom port for the web server in two ways:

1. In your `.env` file:
   ```
   # .env file
   PORT=8080
   ```

2. Using the command-line argument:
   ```
   python main.py --format html --output lineage --port 8080
   ```

The command-line argument takes precedence over the environment variable.

The HTML file is self-contained and can be opened in any modern web browser even without using the built-in server.

### JSON

The JSON output format provides a machine-readable representation of the lineage graph, including all nodes and edges. This is useful for programmatic access or for importing into other tools.

Example command:
```
python main.py --format json --output lineage
```

This will generate `lineage.json` with the following structure:
```json
{
  "nodes": [
    {
      "id": "project1.model1",
      "name": "model1",
      "type": "model",
      "project": "project1",
      "path": "models/model1.sql",
      "compiled_name": "project.dataset.model1"
    },
    ...
  ],
  "edges": [
    {
      "source": "project1.model1",
      "target": "project1.model2",
      "type": "model"
    },
    ...
  ]
}
```

### CSV

The CSV output format generates two files: one for nodes and one for edges. This is useful for importing into spreadsheets, databases, or BI tools for further analysis.

Example command:
```
python main.py --format csv --output lineage
```

This will generate two files:
- `lineage_nodes.csv`: Contains information about all nodes (models and sources)
- `lineage_edges.csv`: Contains information about all edges (dependencies)

## Project Structure

- `main.py`: Entry point of the application
- `src/`: Source code directory
  - `repository_provider.py`: Abstract repository provider interface and implementations
  - `dbt_parser.py`: Parser for dbt project files
  - `lineage_graph.py`: Graph structure for representing lineage
  - `json_generator.py`: Generator for JSON output
  - `csv_generator.py`: Generator for CSV output
  - `html_generator.py`: Generator for interactive HTML visualization
  - `html_template.html`: HTML template for the interactive visualization

## Profiles.yml Integration

The tool can use your dbt profiles.yml file to improve the accuracy of cross-project lineage mapping. This is particularly useful in environments where multiple dbt projects reference each other's models.

### How It Works

1. The tool reads your profiles.yml file (specified by `DBT_PROFILES_PATH`)
2. It extracts the target-specific information (using the target specified by `DBT_PROFILE_TARGET`)
3. When linking sources to models across projects, it:
   - First attempts to match based on the compiled table names from profiles.yml
   - Falls back to name-based inference for any unmatched sources

### Benefits

- **More accurate cross-project lineage**: By using the actual compiled table names, the tool can establish more accurate connections between models across different projects
- **Visual distinction**: In the HTML visualization, connections are color-coded:
  - Solid green lines: Profiles-based cross-project references (high confidence)
  - Dashed purple lines: Inferred cross-project references (lower confidence)

### Configuration

To use this feature, set the following environment variables in your `.env` file:

```
# Path to your dbt profiles.yml file
DBT_PROFILES_PATH=~/.dbt/profiles.yml

# Target environment to use (e.g., dev, prod)
DBT_PROFILE_TARGET=dev
```

## How It Works

1. The tool reads the list of repositories from `repo_list.txt`
2. For each repository, it:
   - Determines whether it's a GitHub repository or a local file path
   - Creates the appropriate repository provider
   - Parses the dbt project files
   - Extracts model dependencies
   - Adds the project to the lineage graph
3. If profiles.yml integration is enabled:
   - The tool reads your profiles.yml file
   - It uses compiled table names to establish cross-project connections
   - It falls back to name-based inference for any remaining unlinked sources
4. If a specific model is selected with `--select`:
   - The tool finds the model across all projects
   - It traces both upstream dependencies and downstream dependents
   - It creates a subgraph containing only the relevant nodes and edges
   - The depth of the lineage traversal can be limited with the `--depth` option
5. Once all projects are processed, it generates output in the specified format (Mermaid diagram, HTML, JSON, or CSV) showing the lineage between models

## Limitations

- The tool currently only supports dbt projects that use the standard structure
- It may not correctly handle all Jinja templating in SQL files
- It assumes that cross-project references use the format `{{ ref('project_name', 'model_name') }}`
- It does not handle circular dependencies

## License

[MIT License](LICENSE)