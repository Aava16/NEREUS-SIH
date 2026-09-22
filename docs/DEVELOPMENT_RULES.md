# NEREUS — Development Rules & Guidelines

## 1. Core Engineering Principles

1. **Keep Modules Small & Comprehensible:**
   - Every file, component, service, or scientific processing script must have a single, well-defined responsibility.
   - Avoid monolithic files (>300 lines should be evaluated for refactoring).

2. **Avoid Giant Components:**
   - Decompose UI into reusable primitives and focused sub-components.
   - Separate visualization logic, shader management, data fetching, and state subscriptions into dedicated hooks and child components.

3. **Strict Layer Separation:**
   - **UI Layer:** Pure presentation, user interaction handling, and reactive rendering.
   - **Business / State Layer:** State management (Zustand), caching policies, and user workflows.
   - **Scientific Processing Layer:** Array slicing, interpolation, unit conversion, and statistical computation (Python backend / WebAssembly where applicable).
   - **Data Access Layer:** API clients on the frontend; SQLAlchemy / xarray repository layers on the backend.

4. **Never Hardcode Datasets in UI Components:**
   - Frontend components must receive data dynamically via API responses or typed mock fixture files during testing.
   - Do not embed arbitrary scientific data arrays or float trajectories inside JSX/TSX files.

5. **Never Invent Scientific Values:**
   - All visualized data must originate from verified observational data (e.g., ARGO, CTD) or validated numerical models.
   - Missing data must be explicitly represented (e.g., `NaN`, null, or quality control flag indicators) rather than filled with fabricated numbers.

6. **Validate Data Assumptions First:**
   - Prior to building visualizations or rendering pipelines, verify coordinate ranges, units, dimensions, and null/fill value conventions.

7. **Prefer Reusable Abstractions:**
   - Build generic coordinate-mapping utilities, colormap interpolators, and chart wrapper components rather than bespoke one-off implementations.

8. **Document Scientific Assumptions:**
   - Explicitly annotate scientific conventions in code docstrings and module documentation:
     - Coordinate systems (e.g., EPSG:4326, standard depth positive down in meters).
     - Physical units ($^\circ\text{C}$, $PSU$, $m/s$, $kg/m^3$).
     - Reference baselines and climatology references used for anomaly calculations.

9. **Extensibility by Design:**
   - Structure variable registries and observation parsers to allow adding new ocean variables (e.g., Dissolved Oxygen, Chlorophyll, pH) and new platform types (e.g., Saildrones, satellite altimetry) without refactoring core components.

10. **Do Not Over-Engineer Prematurely:**
    - Build what is required for each milestone clearly, robustly, and cleanly before introducing speculative complexity.

---

## 2. Code Organization & Standards

### 2.1 Backend Standards (Python / FastAPI)
- **Typing:** Strict Python type hints (`typing`, `Pydantic` models) for all function arguments, return types, and request/response schemas.
- **Async Handling:** Use `async` endpoints for I/O-bound operations; offload heavy CPU/array computations (e.g., xarray slicing of massive NetCDF files) to threadpools or background tasks.
- **Error Handling:** Use standardized HTTP exception responses with clear scientific context (e.g., `DATASET_OUT_OF_BOUNDS`, `VARIABLE_NOT_FOUND`).

### 2.2 Frontend Standards (TypeScript / React)
- **TypeScript:** Strict type checking enabled (`strict: true`). Avoid `any`; define explicit scientific interfaces.
- **State Hygiene:** Keep local state local (`useState`). Use Zustand only for truly global cross-component state (e.g., depth level, active variable, time step).
- **R3F Performance:** 
  - Never allocate objects (vectors, matrices, geometries) inside the `useFrame` render loop.
  - Dispose unused geometries, textures, and materials when components unmount.

---

## 3. Review Checklist for Changes

- [ ] Does the change maintain the separation between metadata (PostgreSQL) and scientific grids (NetCDF/Zarr)?
- [ ] Are all scientific variables clearly typed with explicit units?
- [ ] Does the UI design adhere to the clean, calm scientific aesthetic (avoiding dark/neon clutter)?
- [ ] Are 3D rendering resources properly managed without memory leaks?
- [ ] Is error handling and empty/loading state implemented gracefully?
