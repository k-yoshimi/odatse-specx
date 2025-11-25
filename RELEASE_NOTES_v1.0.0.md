# Release v1.0.0

## 🎉 First Stable Release

We are excited to announce the first stable release of **odatse-specx**, a Python tool for generating and editing AkaiKKR input files with integrated high-entropy alloy (HEA) composition optimization capabilities.

## ✨ Key Features

### Core Functionality

- **AkaiKKR Input File Management**
  - Load AkaiKKR input files as structured data
  - Atom type replacement (by index, coordinates, or label)
  - Define and add new atom species (single or mixed)
  - Export structured data to AkaiKKR input file format
  - Automatic directory creation for output files

- **High-Entropy Alloy Composition Optimization**
  - Integration with ODAT-SE search algorithms
  - Automatic AkaiKKR calculation execution
  - Flexible metric extraction (total energy, band energy, custom patterns)
  - Simplex mode with stick-breaking transformation for normalized compositions
  - Comprehensive error handling with configurable penalty values
  - Support for mock mode for testing without actual calculations

### Advanced Features

- **Metric Extraction**
  - Built-in patterns for `total_energy` and `band_energy`
  - Custom regular expression patterns for arbitrary metrics
  - Metric transformations (identity, abs, log, log1p, sqrt, square)
  - Case-insensitive matching support
  - Flexible group selection for complex patterns

- **Error Handling**
  - Configurable error penalty values
  - Detailed error logging
  - Option to preserve intermediate files for debugging
  - Graceful handling of calculation failures

- **Configuration**
  - TOML-based configuration files
  - Environment variable support for HPC environments
  - Command placeholders for flexible AkaiKKR execution
  - Multiple example configurations included

## 📦 Installation

```bash
# Install from source
git clone https://github.com/k-yoshimi/odatse-specx.git
cd odatse-specx
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.10 or higher
- numpy>=1.20.0
- odat-se

## 🧪 Testing

The project includes a comprehensive test suite with 40 tests covering:
- Input file loading and parsing
- Atom type replacement operations
- Atom species definition
- File writing and directory creation
- Simplex mode transformations
- Metric extraction
- Error handling

Run tests with:
```bash
python -m pytest test/ -v
```

## 📚 Documentation

- **Main README**: Comprehensive overview and quick start guide
- **generate_input.py Documentation**: Detailed API reference
- **optimize_composition.py Documentation**: Parameter manual and usage examples
- **Test Documentation**: Testing guidelines and examples
- **Example Configurations**: 9 pre-configured examples in `examples/` directory

## 🔧 Configuration Examples

The project includes example configurations for:
- 3-element and 5-element alloys
- Total energy and band energy optimization
- Custom metric extraction (magnetization, conductivity)
- Debug mode with intermediate file preservation
- Mock test mode for workflow testing
- HPC environments with environment variables

## 🛠️ Improvements in This Release

- Removed personal settings and paths from configuration files
- Updated `.gitignore` to exclude personal configuration files
- Standardized configuration templates with generic placeholders
- Comprehensive test coverage (40 tests, all passing)
- Clean project structure ready for collaboration

## 📝 Breaking Changes

None. This is the first stable release.

## 🙏 Acknowledgments

This project integrates with [ODAT-SE](https://github.com/k-yoshimi/ODAT-SE) for optimization algorithms and uses [AkaiKKR](https://academeia.github.io/AkaiKKR_Documents/) for first-principles calculations.

## 📄 License

MIT License

## 🔗 Links

- **Repository**: https://github.com/k-yoshimi/odatse-specx
- **Documentation**: See README.md and related documentation files
- **Issues**: https://github.com/k-yoshimi/odatse-specx/issues

---

**Full Changelog**: See git log for detailed commit history.

