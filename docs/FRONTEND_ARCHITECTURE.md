# NEREUS — Frontend Architecture Specification

## 1. Overview & Technology Stack

The NEREUS frontend is a high-performance scientific visualization and analysis application built with modern web technologies:

- **Framework & Build:** React (18+), TypeScript, Vite
- **3D Visualization:** Three.js, React Three Fiber (R3F), `@react-three/drei`
- **Animation & Motion:** 
  - Framer Motion: Layout transitions, modal panels, tab switching, and state reveals.
  - GSAP: Targeted for camera trajectories, coordinate tweens, and complex 3D timeline orchestration.
- **Client & Visualizer State:** Zustand
- **Server State & Caching:** TanStack Query (React Query)
- **Scientific 2D Plotting:** High-precision charting libraries (e.g., Plotly.js / Chart.js / D3) for scientific profiles and T-S diagrams.

---

## 2. Visual Aesthetic & Design System

NEREUS adopts a deliberate **dual-aesthetic model**:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        NEREUS VISUAL SYSTEM                            │
├───────────────────────────────────┬────────────────────────────────────┤
│     Outer Application Frame       │        3D Ocean Visualizer         │
│   (Scientific Calm & Light)       │      (Deep Cinematic Ocean)        │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Clean, breathable scientific UI │ • Rich volumetric depth shading    │
│ • Precise typography & metrics    │ • Dark, atmospheric abyss palette  │
│ • High data density with clarity  │ • Dynamic current particle streams │
│ • Subtle borders, minimal shadows │ • True scientific colormaps        │
│ • Zero cyberpunk / neon clutter   │ • Bathymetric topography & slices  │
└───────────────────────────────────┴────────────────────────────────────┘
```

### Visual Guidelines:
- **Color Scales:** Perceptually uniform scientific colormaps (cmocean palettes: *thermal*, *haline*, *turbid*, *deep*, *dense* alongside standard *viridis* and *plasma*).
- **Motion with Purpose:** Animations strictly communicate spatial orientation, depth descent/ascent, temporal steps, or data state changes. Never gratuitous decoration.
- **Data Integrity:** No hardcoded mock values in UI components. Every visual element represents verified scientific observations or model outputs.

---

## 3. Module & Directory Structure

```text
frontend/src/
├── app/
│   ├── App.tsx                     # Top-level shell and layout provider
│   ├── routes.tsx                  # Module routing (Explore, Observe, Analyze, Data, Validate, Intelligence)
│   └── main.tsx                    # React entry point
├── components/                     # Core design system primitives
│   ├── ui/                         # Buttons, sliders, dropdowns, badges, tooltips
│   ├── layout/                     # Sidebar, header, panel containers, split-views
│   └── scientific/                 # Colormap legends, depth rulers, coordinate readouts
├── features/
│   ├── explore/                    # 3D Ocean Visualizer
│   │   ├── components/             # Canvas, BathymetryMesh, SlicePlane, VectorField, IsoSurface
│   │   ├── shaders/                # Custom GLSL shaders for volume slicing & velocity field
│   │   ├── hooks/                  # useSliceBuffer, useCameraControls, useParticleSystem
│   │   └── store/                  # Visualizer local state (active slice, depth, colormap)
│   ├── observe/                    # In-situ Observations
│   │   ├── components/             # ArgoFloatList, TrajectoryMap, FloatDetailCard, CastPlot
│   │   └── hooks/                  # useArgoFloats, useGliderTracks
│   ├── analyze/                    # Scientific Analytics
│   │   ├── components/             # TsDiagram, VerticalProfileViewer, AnomalyHeatmap, TrendAnalysis
│   │   └── hooks/                  # useProfileData, useRegionalStats
│   ├── data/                       # Datasets & Ingestion
│   │   ├── components/             # DatasetCatalog, IngestionProgress, QualityControlBadge, MetaViewer
│   │   └── hooks/                  # useDatasets, useIngestionJobs
│   ├── validate/                   # Model Validation Engine
│   │   ├── components/             # ValidationMatrix, ResidualPlot, MetricScorecards (MAE, RMSE, Bias, R)
│   │   └── hooks/                  # useValidationRun, useCollocatedData
│   └── intelligence/               # Ocean Intelligence & Predictions
│       ├── components/             # AnomalyAlertList, EddyDetectorView, ForecastComparison
│       └── hooks/                  # useOceanInsights, useForecastTrends
├── hooks/                          # Global utility hooks (useKeyboardShortcuts, useDebounce)
├── stores/                         # Global Zustand stores (globalFilterStore, activeDatasetStore)
├── services/                       # API clients & network layer (FastAPI endpoints)
├── types/                          # Domain TypeScript interfaces & scientific payload types
└── utils/                          # Coordinate transforms, colormap math, formatting helpers
```

---

## 4. 3D WebGL / R3F Rendering Strategy

1. **Bathymetric Base Layer:**
   - Pre-generated or tiled digital elevation model (DEM) of ocean bathymetry.
   - Low-overhead custom shader incorporating depth-dependent lighting and fog.
2. **Volumetric Slices:**
   - Planar 2D slice textures rendered dynamically in 3D space at arbitrary depth levels ($Z$) or arbitrary vertical transect lines.
   - Colormapped on the GPU via fragment shaders using LUT (Lookup Table) textures.
3. **Current Vector Particle System:**
   - Instanced meshes or GPU point particles simulating velocity fields derived from $(U, V, W)$ components.
   - Lifetime and velocity updated smoothly according to timestep.
4. **Camera Management:**
   - Smooth transitions between geographic regions (e.g., Arabian Sea, Bay of Bengal, Equatorial Indian Ocean) driven by GSAP camera tweens.

---

## 5. State Management Architecture

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        STATE SEPARATION MODEL                          │
├───────────────────────────────────┬────────────────────────────────────┤
│         TanStack Query            │           Zustand Stores           │
│         (Server State)            │           (Client State)           │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Dataset metadata & catalogs     │ • Selected depth level (e.g. 500m) │
│ • Sliced 2D/3D array payloads     │ • Active variable (Temp / Salinity)│
│ • ARGO float trajectory points    │ • Time scrubber position & playing │
│ • In-situ vertical profile curves │ • Active colormap & range clamping │
│ • Validation metrics & stats      │ • Layer toggles (Slices, Vectors)  │
│ • Automated caching & refetching  │ • Camera viewpoint & focus region  │
└───────────────────────────────────┴────────────────────────────────────┘
```
