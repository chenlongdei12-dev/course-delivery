import Foundation
import AVFoundation
import AppKit

struct RangeSpec:Decodable{let `in`:Double;let out:Double}
struct Chapter:Decodable{let id:String;let title:String;let ranges:[RangeSpec]}
struct Manifest:Decodable{let source:String;let output_dir:String;let preset:String?;let chapters:[Chapter]}
guard CommandLine.arguments.count>=2 else{fatalError("Usage: swift verify_outputs.swift manifest.json [qc-dir]")}
let m=try JSONDecoder().decode(Manifest.self,from:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1])))
let qc=URL(fileURLWithPath:CommandLine.arguments.count>2 ? CommandLine.arguments[2] : m.output_dir+"_qc",isDirectory:true);try FileManager.default.createDirectory(at:qc,withIntermediateDirectories:true)
func safe(_ s:String)->String{s.components(separatedBy:CharacterSet(charactersIn:"/\\:*?\"<>|")).joined(separator:"_")}
var results:[[String:Any]]=[];var failures=0
for ch in m.chapters{
 let file="\(safe(ch.id))_\(safe(ch.title)).mp4",url=URL(fileURLWithPath:m.output_dir).appendingPathComponent(file),expected=ch.ranges.reduce(0){$0+$1.out-$1.in}
 var row:[String:Any]=["chapter_id":ch.id,"file":file,"expected_duration_sec":expected]
 guard FileManager.default.fileExists(atPath:url.path) else{row["status"]="missing";failures+=1;results.append(row);continue}
 let asset=AVURLAsset(url:url),duration=try await asset.load(.duration).seconds,vs=try await asset.loadTracks(withMediaType:.video),as_=try await asset.loadTracks(withMediaType:.audio)
 let bytes=(try FileManager.default.attributesOfItem(atPath:url.path)[.size] as? Int64) ?? 0, delta=abs(duration-expected), ok=bytes>0 && !vs.isEmpty && !as_.isEmpty && delta<=0.25
 row.merge(["actual_duration_sec":duration,"duration_delta_sec":delta,"bytes":bytes,"video_tracks":vs.count,"audio_tracks":as_.count,"status":ok ? "pass":"fail"]){$1};if !ok{failures+=1}
 if !vs.isEmpty {let gen=AVAssetImageGenerator(asset:asset);gen.appliesPreferredTrackTransform=true;gen.maximumSize=CGSize(width:960,height:540);var times=[1.0,max(1,duration-1)];var cursor=0.0;for r in ch.ranges.dropLast(){cursor += r.out-r.in;times += [max(0,cursor-0.5),min(duration-0.01,cursor+0.5)]};for sec in times{let(cg,_)=try await gen.image(at:CMTime(seconds:sec,preferredTimescale:600));let png=NSBitmapImageRep(cgImage:cg).representation(using:.png,properties:[:])!;try png.write(to:qc.appendingPathComponent(String(format:"%@_%08.3f.png",safe(ch.id),sec)))}}
 results.append(row)
}
let report:[String:Any]=["expected_outputs":m.chapters.count,"checked_outputs":results.count,"failures":failures,"status":failures==0 ? "pass":"fail","results":results]
try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:qc.appendingPathComponent("verification.json"));print("checked=\(results.count) failures=\(failures)");if failures>0{exit(2)}
