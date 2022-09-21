import { createPluginUI } from 'molstar/lib/mol-plugin-ui/react18';
import { PluginUIContext } from 'molstar/lib/mol-plugin-ui/context';
import { DefaultPluginUISpec } from 'molstar/lib/mol-plugin-ui/spec';
import { PluginConfig } from 'molstar/lib/mol-plugin/config';
import { StateBuilder, StateObjectSelector, StateTransform, StateTransformer } from 'molstar/lib/mol-state';
import { PluginStateObject } from 'molstar/lib/mol-plugin-state/objects';
import { StateTransforms } from 'molstar/lib/mol-plugin-state/transforms';
import { createVolumeRepresentationParams } from 'molstar/lib/mol-plugin-state/helpers/volume-representation-params';
import { Grid, Volume } from 'molstar/lib/mol-model/volume';
import { Color } from 'molstar/lib/mol-util/color';
import { ParamDefinition as PD } from 'molstar/lib/mol-util/param-definition';
import { CustomProperties } from 'molstar/lib/mol-model/custom-property';
import { BehaviorSubject } from 'rxjs';
import { setSubtreeVisibility } from 'molstar/lib/mol-plugin/behavior/static/state';
import { CifBlock, CifFile } from 'molstar/lib/mol-io/reader/cif';

import * as MeshExamples from './mesh-extension/examples'
import { ColorNames, Mesh } from './mesh-extension/molstar-lib-imports';
import { type Metadata, Annotation, Segment } from './volume-api-client-lib/data';
import { VolumeApiV1 } from './volume-api-client-lib/volume-api';


const DEFAULT_DETAIL: number | null = null;  // null means worst

const USE_GHOST_NODES = false;

const API = new VolumeApiV1();


namespace Metadata {
    export function meshSegments(metadata: Metadata): number[] {
        const segmentIds = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        if (segmentIds === undefined) return [];
        return Object.keys(segmentIds).map(s => parseInt(s));
    }
    export function meshSegmentDetails(metadata: Metadata, segmentId: number): number[] {
        const segmentIds = metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids;
        if (segmentIds === undefined) return [];
        const details = segmentIds[segmentId].detail_lvls;
        return Object.keys(details).map(s => parseInt(s));
    }
    /** Get the worst available detail level that is not worse than preferredDetail. 
     * If preferredDetail is null, get the worst detail level overall.
     * (worse = greater number) */
    export function getSufficientDetail(metadata: Metadata, segmentId: number, preferredDetail: number | null) {
        let availDetails = meshSegmentDetails(metadata, segmentId);
        if (preferredDetail !== null) {
            availDetails = availDetails.filter(det => det <= preferredDetail);
        }
        return Math.max(...availDetails);
    }
    export function annotationsBySegment(metadata: Metadata): { [id: number]: Segment } {
        const result: { [id: number]: Segment } = {};
        for (const segment of metadata.annotation.segment_list) {
            if (segment.id in result) {
                throw new Error(`Duplicate segment annotation for segment ${segment.id}`);
            }
            result[segment.id] = segment;
        }
        return result;
    }
    export function dropSegments(metadata: Metadata, segments: number[]): void {
        if (metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids === undefined) return;
        const dropSet = new Set(segments);
        metadata.annotation.segment_list = metadata.annotation.segment_list.filter(seg => !dropSet.has(seg.id));
        for (const seg of segments) {
            delete metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids[seg];
        }
    }
}


type DataSource = '' | 'xEmdb' | 'xBioimage' | 'xMeshes' | 'xMeshStreaming' | 'xAuto';


export class AppModel {
    public entryId = new BehaviorSubject<string>('');
    public annotation = new BehaviorSubject<Annotation | undefined>(undefined);
    public currentSegment = new BehaviorSubject<Segment | undefined>(undefined);
    public error = new BehaviorSubject<any>(undefined);
    public dataSource = new BehaviorSubject<DataSource>('');

    private plugin: PluginUIContext = undefined as any;

    private volume?: Volume;  // TODO optional
    private currentLevel: any[] = [];

    private segmentation?: LatticeSegmentation;

    private metadata?: Metadata = undefined;
    private meshSegmentNodes: { [segid: number]: any } = {};

    private currentSegments: any[] = [];
    private volumeRepr: any = undefined;



    async init(target: HTMLElement) {
        const defaultSpec = DefaultPluginUISpec();
        this.plugin = await createPluginUI(target, {
            ...defaultSpec,
            layout: {
                initial: {
                    isExpanded: false,
                    showControls: true,  // original: false
                    controlsDisplay: 'landscape',  // original: not given
                },
            },
            components: {
                // controls: { left: 'none', right: 'none', top: 'none', bottom: 'none' },
                controls: { right: 'none', top: 'none', bottom: 'none' },
            },
            canvas3d: {
                camera: {
                    helper: { axes: { name: 'off', params: {} } }
                }
            },
            config: [
                [PluginConfig.Viewport.ShowExpand, true],  // original: false
                [PluginConfig.Viewport.ShowControls, true],  // original: false
                [PluginConfig.Viewport.ShowSelectionMode, false],
                [PluginConfig.Viewport.ShowAnimation, false],
            ],
        });

        
        // setTimeout(() => this.loadExampleEmdb(), 50);
        setTimeout(() => this.loadExampleAuto(), 50);
        
        // const entryFromURL = window.location.hash.replace('#', '') || undefined;
        // setTimeout(() => this.loadExampleMeshes(entryFromURL), 50);
    }

    async loadExampleEmdb(entryId: string = 'emd-1832') {
        const isoLevel = 2.73;
        const source = AppModel.splitEntryId(entryId).source as 'empiar'|'emdb';
        // const url = `https://maps.rcsb.org/em/${entryId}/cell?detail=6`;
        const url = API.volumeServerRequestUrl(source, entryId, 0, [[-1000, -1000, -1000], [1000, 1000, 1000]], 100000000);
        const { plugin } = this;

        await plugin.clear();

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data, { entryId });
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;

        const cif = await plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
        const segmentationBlock = cif.data!.blocks.find(b => b.header === 'SEGMENTATION_DATA');

        this.metadata = await API.getMetadata(source, entryId);

        console.log('annotation:', this.metadata.annotation);

        this.entryId.next(entryId);
        this.annotation.next(this.metadata.annotation);
        this.segmentation = new LatticeSegmentation(segmentationBlock!, this.volume.grid);

        const repr = plugin.build();

        repr
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel, 'relative') },
                color: 'uniform',
                colorParams: { value: Color(0x121212) }
            }));

        await repr.commit();

        await this.showSegments(this.metadata.annotation.segment_list);

        this.dataSource.next('xEmdb');
    }

    async loadExampleBioimage() {
        const entryId = 'emd-99999';
        const url = API.volumeServerRequestUrl('emdb', entryId, 0, [[-1000, -1000, -1000], [1000, 1000, 1000]], 10000000);
        // http://localhost:9000/v1/emdb/emd-99999/box/0/-10000/-10000/-10000/10000/10000/10000/10000000
        const { plugin } = this;

        await plugin.clear();

        const data = await plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
        const parsed = await plugin.dataFormats.get('dscif')!.parse(plugin, data);
        const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
        const volumeData = volume.cell!.obj!.data;
        this.volume = volumeData;

        this.volumeRepr = plugin.build()
            .to(volume)
            .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                type: 'isosurface',
                typeParams: { alpha: 1.0, isoValue: Volume.IsoValue.relative(-0.55) },
                color: 'uniform',
                colorParams: { value: Color(0x224899) }
            }));
        await this.volumeRepr.commit();

        this.currentSegments = [];
        // const segP = this.createSegment99999Plus(volumeData, 0);
        // const segM = this.createSegment99999Minus(volumeData, -0.55);
        // await this.showSegment(segP, [0.3, 0.7, 0.1]);
        // await this.showSegment(segM, [0.1, 0.3, 0.7]);

        this.dataSource.next('xBioimage');
    }

    async loadExampleMeshes(entryId: string = 'empiar-10070', segments: 'fg'|'all' = 'fg') {
        const source = AppModel.splitEntryId(entryId).source;
        let error = undefined;

        try {
            await this.plugin.clear();
            // Testing API:
            // try {
            //     const meshes = await this.getMeshData_debugging('empiar', 'empiar-10070', 1, 7);
            //     console.log('Meshes from API:\n', meshes);
            // } catch {
            //     console.error('Could not get mesh data from API (maybe API not running?)');
            // }
            // await this.plugin.clear();

            // Examples for mesh visualization - currently taking static data stored on a MetaCentrum VM
            // MeshExamples.runMeshExample(this.plugin, 'fg', 'http://sestra.ncbr.muni.cz/data/cellstar-sample-data/db');
            // MeshExamples.runMultimeshExample(this.plugin, 'fg', 'worst', 'http://sestra.ncbr.muni.cz/data/cellstar-sample-data/db');  // Multiple segments merged into 1 segment with multiple meshes

            this.metadata = await API.getMetadata(source, entryId);
            if (segments === 'fg') {
                const bgSegments = [13, 15];
                Metadata.dropSegments(this.metadata, bgSegments);
            }

            for (let segment of this.metadata!.annotation.segment_list) {
                const detail = Metadata.getSufficientDetail(this.metadata!, segment.id, DEFAULT_DETAIL);
                // console.log(`Annotation: segment ${segment.id}. ${segment.biological_annotation.name} ${segment.colour} ${detail}`);
                // QUESTION: hmm, shouldn't it be "color"?
            }

            this.meshSegmentNodes = {};
            this.showMeshSegments(this.metadata!.annotation.segment_list, entryId);
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            window.location.hash = entryId;
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.dataSource.next('xMeshes');
            this.error.next(error);
        }
    }

    async loadExampleMeshStreaming(entryId: string = 'empiar-10070') {
        const source = AppModel.splitEntryId(entryId).source as 'empiar'|'emdb';
        let error = undefined;

        try {
            await this.plugin.clear();
            this.metadata = await API.getMetadata(source, entryId);
            MeshExamples.runMeshStreamingExample(this.plugin, source, entryId);
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            window.location.hash = entryId;
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.dataSource.next('xMeshStreaming');
            this.error.next(error);
        }
    }

    async loadExampleAuto(entryId: string = 'emd-1832') {
        const source = AppModel.splitEntryId(entryId).source as 'empiar'|'emdb';
        let error = undefined;

        try {
            await this.plugin.clear();
            this.metadata = await API.getMetadata(source, entryId);
            console.log(this.metadata.grid);

            let hasVolumes = this.metadata.grid.volumes.volume_downsamplings.length > 0;
            const hasLattices = this.metadata.grid.segmentation_lattices.segmentation_lattice_ids.length > 0;
            const hasMeshes = this.metadata.grid.segmentation_meshes.mesh_component_numbers.segment_ids !== undefined;
            if (hasVolumes && !hasLattices){
                // TODO skip this tweak once the API is ready
                console.log('WARNING: No lattices available, ignoring volume (waiting for API changes)');
                hasVolumes = false;
            }

            const BOX: [[number, number, number], [number, number, number]] = [[-1000, -1000, -1000], [1000, 1000, 1000]];
            const MAX_VOXELS = 100_000_000;

            if (hasVolumes) {
                const isoLevel = 2.73; // TODO choose isoLevel smartly (2.73 is OK for emd-1832)
                const url = API.volumeServerRequestUrl(source, entryId, 0, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
                const parsed = await this.plugin.dataFormats.get('dscif')!.parse(this.plugin, data, { entryId });
                const volume: StateObjectSelector<PluginStateObject.Volume.Data> = parsed.volumes?.[0] ?? parsed.volume;
                const volumeData = volume.cell!.obj!.data;
                this.volume = volumeData;
                const repr = await this.plugin.build()
                    .to(volume)
                    .apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volumeData, {
                        type: 'isosurface',
                        typeParams: { alpha: 0.2, isoValue: Volume.adjustedIsoValue(volumeData, isoLevel, 'relative') },
                        color: 'uniform',
                        colorParams: { value: Color(0x121212) }
                    }))
                    .commit();
            }
            if (hasLattices) {
                const url = API.volumeServerRequestUrl(source, entryId, 0, BOX, MAX_VOXELS);
                const data = await this.plugin.builders.data.download({ url, isBinary: true }, { state: { isGhost: USE_GHOST_NODES } });
                const cif = await this.plugin.build().to(data).apply(StateTransforms.Data.ParseCif).commit();
                AppModel.logCifOverview(cif.data!); // TODO when could cif.data be undefined?
                const latticeBlock = cif.data!.blocks.find(b => b.header === 'SEGMENTATION_DATA');
                if (latticeBlock){
                    if (!this.volume) throw new Error('Volume data must be present to create lattice segmentation'); // TODO create grid without volume data
                    this.segmentation = new LatticeSegmentation(latticeBlock, this.volume.grid);
                    await this.showSegments(this.metadata.annotation.segment_list);
                } else {
                    console.log('WARNING: Block SEGMENTATION_DATA is missing. Not showing segmentations.');
                }

            }
            if (hasMeshes) {
                MeshExamples.runMeshStreamingExample(this.plugin, source, entryId);
            }
        } catch (ex) {
            this.metadata = undefined;
            error = ex;
            throw ex;
        } finally {
            window.location.hash = entryId;
            this.entryId.next(entryId);
            this.annotation.next(this.metadata?.annotation);
            this.dataSource.next('xAuto');
            this.error.next(error);
        }

    }

    /** Make visible the specified set of lattice segments */
    async showSegments(segments: Segment[]) {
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        const update = this.plugin.build();

        for (const l of this.currentLevel) update.delete(l);
        this.currentLevel = [];

        for (const s of segments) {
            const volume = this.segmentation?.createSegment(s.id);
            const root = update.toRoot().apply(CreateVolume, { volume });
            this.currentLevel.push(root.selector);

            root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
                type: 'isosurface',
                typeParams: { alpha: 1, isoValue: Volume.IsoValue.absolute(0.95) },
                color: 'uniform',
                colorParams: { value: Color.fromNormalizedArray(s.colour, 0) }
            }));
        }

        // const controlPoints: Vec2[] = [
        //     Vec2.create(0, 0),
        //     Vec2.create(0.5, 0),
        //     Vec2.create(0.98, 1),
        //     Vec2.create(1.1, 1),
        // ]

        // // const list = {
        // //     kind: 'interpolate' as const,
        // //     colors: [
        // //         [Color(0x0), 0]
        // //     ]
        // // }

        // root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
        //     type: 'direct-volume',
        //     typeParams: { 
        //         ignoreLight: true,
        //         stepsPerCell: 1,
        //         controlPoints,
        //         xrayShaded: false,
        //     },
        //     color: 'uniform',
        //     colorParams: { value: Color(Math.round(Math.random() * 0xffffff)) }
        // }));

        await update.commit();
    }

    /** Make visible the specified set of mesh segments */
    async showMeshSegments(segments: Segment[], entryId: string) {
        if (segments.length === 1) {
            this.currentSegment.next(segments[0]);
        } else {
            this.currentSegment.next(undefined);
        }

        for (const node of Object.values(this.meshSegmentNodes)) {
            setSubtreeVisibility(node.state!, node.ref, true);  // hide
        }
        for (const seg of segments) {
            let node = this.meshSegmentNodes[seg.id];
            if (!node) {
                const detail = Metadata.getSufficientDetail(this.metadata!, seg.id, DEFAULT_DETAIL);
                const color = seg.colour.length >= 3 ? Color.fromNormalizedArray(seg.colour, 0) : ColorNames.gray;
                node = await MeshExamples.createMeshFromUrl(this.plugin, API.meshServerRequestUrl(AppModel.splitEntryId(entryId).source, entryId, seg.id, detail), seg.id, detail, true, false, color);
                this.meshSegmentNodes[seg.id] = node;
            }
            setSubtreeVisibility(node.state!, node.ref, false);  // show
        }
    }

    /** Change isovalue for existing volume representation (in Bioimage example) */
    async setIsoValue(newValue: number, showSegmentation: boolean) {
        if (!this.volumeRepr) return;

        const { plugin } = this;
        await plugin.build().to(this.volumeRepr).update(createVolumeRepresentationParams(this.plugin, this.volume, {
            type: 'isosurface',
            typeParams: { alpha: showSegmentation ? 0.0 : 1, isoValue: Volume.IsoValue.relative(newValue) },
            color: 'uniform',
            colorParams: { value: showSegmentation ? Color(0x777777) : Color(0x224899) }
        })).commit();

        const update = this.plugin.build();

        for (const l of this.currentSegments) update.delete(l);
        this.currentSegments = [];
        await update.commit();

        if (showSegmentation) {
            const segP = this.createSegment99999Plus(this.volume!, -0.35);
            const segM = this.createSegment99999Minus(this.volume!, newValue);
            await this.showSegment(segP, [0.3, 0.7, 0.6], 0.5);
            await this.showSegment(segM, [0.1, 0.3, 0.7]);
        }

    }

    /** Split entry ID (e.g. 'emd-1832') into source ('emdb') and number ('1832') */
    static splitEntryId(entryId: string) {
        const PREFIX_TO_SOURCE: { [prefix: string]: string } = { 'empiar': 'empiar', 'emd': 'emdb' };
        const [prefix, entry] = entryId.split('-');
        return {
            source: PREFIX_TO_SOURCE[prefix],
            entryNumber: entry
        };
    }

    /** Create entry ID (e.g. 'emd-1832') for a combination of source ('emdb') and number ('1832') */
    static createEntryId(source: string, entryNumber: string | number) {
        const SOURCE_TO_PREFIX: { [prefix: string]: string } = { 'empiar': 'empiar', 'emdb': 'emd' };
        return `${SOURCE_TO_PREFIX[source]}-${entryNumber}`;
    }



    private createFakeSegment(volume: Volume, level: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            if (Math.floor(10 * i / space.dimensions[0]) !== level) continue;

            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > 2.5) newData[o] = 1;
                }
            }
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private createSegment99999Plus(volume: Volume, threshold: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > threshold) newData[o] = 1;
                }
            }
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private createSegment99999Minus(volume: Volume, threshold: number): Volume {
        const { mean, sigma } = volume.grid.stats;
        const { data, space } = volume.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < space.dimensions[0]; i++) {
            for (let j = 0; j < space.dimensions[1]; j++) {
                for (let k = 0; k < space.dimensions[2]; k++) {
                    const o = space.dataOffset(i, j, k);
                    const v = (data[o] - mean) / sigma;
                    if (v > threshold && v < -0.35) newData[o] = 1;
                }
            }
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...volume.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...volume.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private async showSegment(volume: Volume, color: number[], opacity = 1) {
        const update = this.plugin.build();
        const root = update.toRoot().apply(CreateVolume, { volume });
        this.currentLevel.push(root.selector);

        const seg = root.apply(StateTransforms.Representation.VolumeRepresentation3D, createVolumeRepresentationParams(this.plugin, volume, {
            type: 'isosurface',
            typeParams: { alpha: opacity, isoValue: Volume.IsoValue.absolute(0.95), transparentBackfaces: 'off', doubleSided: false, flatShaded: true },
            color: 'uniform',
            colorParams: { value: Color.fromNormalizedArray(color, 0) }
        }));

        this.currentSegments.push(seg.selector);

        await update.commit();
    }



    private logStuff(plugin: PluginUIContext, repr: StateBuilder.Root): void {
        console.log('plugin:\n', plugin);
        console.log('repr:\n', repr);
        console.log('tree:\n', repr.currentTree);
        console.log('children:', repr.currentTree.children.size);
    }

    private static logCifOverview(cifData: CifFile): void {
        const MAX_VALUES = 5;
        console.log('cifData.name:', cifData.name);
        cifData.blocks.forEach(block => {
            console.log(`    ${block.header}`);
            block.categoryNames.forEach(catName => {
                const category = block.categories[catName];
                const nRows = category.rowCount;
                console.log(`        _${catName} [${nRows} rows]`);
                category.fieldNames.forEach(fieldName => {
                    const field = category.getField(fieldName);
                    let values = field?.toStringArray().slice(0, MAX_VALUES).join(', ');
                    if (nRows > MAX_VALUES) values += '...';
                    console.log(`            .${fieldName}:  ${values}`);
                });
            });
        });
    }

}

class LatticeSegmentation {
    private segmentationValues: ReadonlyArray<number>;
    private segmentMap;
    private grid: Grid;

    public constructor(segmentationDataBlock: CifBlock, grid: Grid) {
        this.segmentationValues = segmentationDataBlock!.categories['segmentation_data_3d'].getField('values')?.toIntArray()!;
        this.segmentMap = LatticeSegmentation.makeSegmentMap(segmentationDataBlock);
        this.grid = grid;
    }

    public createSegment(segId: number): Volume {
        const { mean, sigma } = this.grid.stats;
        const { data, space } = this.grid.cells;
        const newData = new Float32Array(data.length);

        for (let i = 0; i < data.length; i++) {
            newData[i] = this.segmentMap.get(this.segmentationValues[i])?.has(segId) ? 1 : 0;
        }

        return {
            sourceData: { kind: 'custom', name: 'test', data: newData as any },
            customProperties: new CustomProperties(),
            _propertyData: {},
            grid: {
                ...this.grid,
                //stats: { min: 0, max: 1, mean: newMean, sigma: arrayRms(newData) },
                stats: { min: 0, max: 1, mean: 0, sigma: 1 },
                cells: {
                    ...this.grid.cells,
                    data: newData as any,
                }
            }
        };
    }

    private static makeSegmentMap(segmentationDataBlock: CifBlock): Map<number, Set<number>> {
        const setId = segmentationDataBlock.categories['segmentation_data_table'].getField('set_id')?.toIntArray()!; 
        const segmentId = segmentationDataBlock.categories['segmentation_data_table'].getField('segment_id')?.toIntArray()!;
        const map = new Map<number, Set<number>>();
        for (let i = 0; i < segmentId.length; i++) {
            if (!map.has(setId[i])) {
                map.set(setId[i], new Set());
            }
            map.get(setId[i])!.add(segmentId[i]);
        }
        return map;
    }
}




const CreateTransformer = StateTransformer.builderFactory('cellstar');

const CreateVolume = CreateTransformer({
    name: 'create-transformer',
    from: PluginStateObject.Root,
    to: PluginStateObject.Volume.Data,
    params: {
        volume: PD.Value<Volume>(undefined as any, { isHidden: true }),
    }
})({
    apply({ params }) {
        return new PluginStateObject.Volume.Data(params.volume);
    }
})