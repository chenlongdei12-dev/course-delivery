import Foundation
import AVFoundation

struct RangeSpec:Decodable{let `in`:Double;let out:Double}
struct Chapter:Decodable{let id:String;let title:String;let ranges:[RangeSpec]}
struct Manifest:Decodable{let source:String;let output_dir:String;let preset:String?;let chapters:[Chapter]}
guard CommandLine.arguments.count==2 else{fatalError("Usage: swift render_chapters.swift /path/manifest.json")}
let manifest=try JSONDecoder().decode(Manifest.self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
let sourceURL=URL(fileURLWithPath:manifest.source), outDir=URL(fileURLWithPath:manifest.output_dir,isDirectory:true)
try FileManager.default.createDirectory(at:outDir,withIntermediateDirectories:true)
let asset=AVURLAsset(url:sourceURL), duration=try await asset.load(.duration).seconds
guard let sv=try await asset.loadTracks(withMediaType:.video).first,let sa=try await asset.loadTracks(withMediaType:.audio).first else{fatalError("Source must contain video and audio")}
let preset:[String:String]=["1080p":AVAssetExportPreset1920x1080,"720p":AVAssetExportPreset1280x720,"highest":AVAssetExportPresetHighestQuality,"passthrough":AVAssetExportPresetPassthrough]
let chosen=preset[manifest.preset ?? "1080p"] ?? AVAssetExportPreset1920x1080
func safe(_ s:String)->String{s.components(separatedBy:CharacterSet(charactersIn:"/\\:*?\"<>|")).joined(separator:"_")}
var log:[[String:Any]]=[]
for (idx,ch) in manifest.chapters.enumerated(){
 guard !ch.ranges.isEmpty else{fatalError("\(ch.id) has no ranges")}
 for r in ch.ranges {guard r.in>=0 && r.out>r.in && r.out<=duration+0.05 else{fatalError("Invalid range in \(ch.id): \(r.in)-\(r.out), source duration \(duration)")}}
 let comp=AVMutableComposition(); guard let v=comp.addMutableTrack(withMediaType:.video,preferredTrackID:kCMPersistentTrackID_Invalid),let a=comp.addMutableTrack(withMediaType:.audio,preferredTrackID:kCMPersistentTrackID_Invalid) else{fatalError("Cannot create tracks")}; v.preferredTransform=try await sv.load(.preferredTransform)
 var cursor=CMTime.zero
 for r in ch.ranges {let tr=CMTimeRange(start:CMTime(seconds:r.in,preferredTimescale:600),duration:CMTime(seconds:r.out-r.in,preferredTimescale:600));try v.insertTimeRange(tr,of:sv,at:cursor);try a.insertTimeRange(tr,of:sa,at:cursor);cursor=CMTimeAdd(cursor,tr.duration)}
 let file="\(safe(ch.id))_\(safe(ch.title)).mp4", url=outDir.appendingPathComponent(file)
 if FileManager.default.fileExists(atPath:url.path){
  let existing=(try FileManager.default.attributesOfItem(atPath:url.path)[.size] as? Int64) ?? 0
  if existing>0 {print("skip existing \(file)");continue}
  try FileManager.default.removeItem(at:url)
 }
 guard let ex=AVAssetExportSession(asset:comp,presetName:chosen) else{fatalError("Cannot create exporter")}; ex.shouldOptimizeForNetworkUse = true
 print("[\(idx+1)/\(manifest.chapters.count)] \(file)"); try await ex.export(to:url,as:.mp4)
 let bytes=(try FileManager.default.attributesOfItem(atPath:url.path)[.size] as? Int64) ?? 0
 log.append(["chapter_id":ch.id,"file":file,"expected_duration_sec":cursor.seconds,"bytes":bytes,"status":"completed"])
}
try JSONSerialization.data(withJSONObject:["source":manifest.source,"preset":manifest.preset ?? "1080p","outputs":log],options:[.prettyPrinted,.sortedKeys]).write(to:outDir.appendingPathComponent("render_log.json"))
print("completed")
