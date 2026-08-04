import AppKit
import Foundation

enum AssetBuildError: Error, CustomStringConvertible {
    case usage
    case unreadableImage(String)
    case encodingFailed(String)

    var description: String {
        switch self {
        case .usage:
            return "usage: swift tools/build_assets.swift INPUT_DIR OUTPUT_DIR"
        case .unreadableImage(let path):
            return "cannot read image: \(path)"
        case .encodingFailed(let path):
            return "cannot encode image: \(path)"
        }
    }
}

func loadImage(_ url: URL) throws -> NSImage {
    guard let image = NSImage(contentsOf: url) else {
        throw AssetBuildError.unreadableImage(url.path)
    }
    return image
}

func render(size: NSSize, drawing: () -> Void) throws -> NSBitmapImageRep {
    guard let bitmap = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: Int(size.width),
        pixelsHigh: Int(size.height),
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bitmapFormat: [],
        bytesPerRow: 0,
        bitsPerPixel: 0
    ), let context = NSGraphicsContext(bitmapImageRep: bitmap) else {
        throw AssetBuildError.encodingFailed("in-memory canvas")
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = context
    NSColor.clear.setFill()
    NSRect(origin: .zero, size: size).fill()
    context.imageInterpolation = .high
    drawing()
    context.flushGraphics()
    NSGraphicsContext.restoreGraphicsState()
    return bitmap
}

func write(
    _ bitmap: NSBitmapImageRep,
    as type: NSBitmapImageRep.FileType,
    properties: [NSBitmapImageRep.PropertyKey: Any],
    to url: URL
) throws {
    guard let data = bitmap.representation(using: type, properties: properties) else {
        throw AssetBuildError.encodingFailed(url.path)
    }
    try data.write(to: url, options: .atomic)
}

func drawLabel(_ text: String, x: CGFloat) {
    let background = NSRect(x: x, y: 20, width: 112, height: 38)
    NSColor(calibratedWhite: 0.04, alpha: 0.78).setFill()
    NSBezierPath(roundedRect: background, xRadius: 5, yRadius: 5).fill()

    let attributes: [NSAttributedString.Key: Any] = [
        .font: NSFont.monospacedSystemFont(ofSize: 16, weight: .semibold),
        .foregroundColor: NSColor.white
    ]
    text.draw(at: NSPoint(x: x + 12, y: 29), withAttributes: attributes)
}

func build(inputDirectory: URL, outputDirectory: URL) throws {
    let fileManager = FileManager.default
    let companyDirectory = outputDirectory.appendingPathComponent("companies", isDirectory: true)
    let publicationDirectory = outputDirectory.appendingPathComponent("publications", isDirectory: true)
    try fileManager.createDirectory(at: companyDirectory, withIntermediateDirectories: true)
    try fileManager.createDirectory(at: publicationDirectory, withIntermediateDirectories: true)

    let standardInput = inputDirectory.appendingPathComponent("standard-robotics.png")
    let standardOutput = companyDirectory.appendingPathComponent("standard-robotics.png")
    if fileManager.fileExists(atPath: standardOutput.path) {
        try fileManager.removeItem(at: standardOutput)
    }
    try fileManager.copyItem(at: standardInput, to: standardOutput)

    let deepano = try loadImage(inputDirectory.appendingPathComponent("deepano-wordmark.png"))
    let deepanoBitmap = try render(size: NSSize(width: 400, height: 126)) {
        deepano.draw(
            in: NSRect(x: 0, y: 0, width: 400, height: 126),
            from: NSRect(origin: .zero, size: deepano.size),
            operation: .sourceOver,
            fraction: 1
        )
    }
    try write(
        deepanoBitmap,
        as: .png,
        properties: [:],
        to: companyDirectory.appendingPathComponent("deepano.png")
    )

    let definesys = try loadImage(inputDirectory.appendingPathComponent("definesys-logo.png"))
    let definesysBitmap = try render(size: NSSize(width: 190, height: 78)) {
        definesys.draw(
            in: NSRect(x: 0, y: 0, width: 190, height: 78),
            from: NSRect(x: 0, y: 0, width: 190, height: 78),
            operation: .sourceOver,
            fraction: 1
        )
    }
    try write(
        definesysBitmap,
        as: .png,
        properties: [:],
        to: companyDirectory.appendingPathComponent("definesys.png")
    )

    // Profile avatars (zhiyuan-xiao.jpg + zhiyuan-xiao-hover.jpg) are built by
    // tools/build_profile.py — a cross-platform face-aware square crop (Pillow + OpenCV).

    let source = try loadImage(inputDirectory.appendingPathComponent("aurora-source.jpg"))
    let output = try loadImage(inputDirectory.appendingPathComponent("aurora-output.jpg"))
    let cropWidth: CGFloat = 640
    let sourceCropX = (source.size.width - cropWidth) / 2
    let outputCropX = (output.size.width - cropWidth) / 2

    let comparison = try render(size: NSSize(width: 1280, height: 720)) {
        source.draw(
            in: NSRect(x: 0, y: 0, width: 640, height: 720),
            from: NSRect(x: sourceCropX, y: 0, width: cropWidth, height: 720),
            operation: .sourceOver,
            fraction: 1
        )
        output.draw(
            in: NSRect(x: 640, y: 0, width: 640, height: 720),
            from: NSRect(x: outputCropX, y: 0, width: cropWidth, height: 720),
            operation: .sourceOver,
            fraction: 1
        )
        NSColor(calibratedWhite: 1, alpha: 0.92).setFill()
        NSRect(x: 638, y: 0, width: 4, height: 720).fill()
        drawLabel("SOURCE", x: 20)
        drawLabel("AURORA", x: 1148)
    }
    try write(
        comparison,
        as: .jpeg,
        properties: [.compressionFactor: 0.82],
        to: publicationDirectory.appendingPathComponent("aurora-before-after.jpg")
    )
}

do {
    guard CommandLine.arguments.count == 3 else {
        throw AssetBuildError.usage
    }
    let input = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
    let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
    try build(inputDirectory: input, outputDirectory: output)
    print("assets built")
} catch {
    FileHandle.standardError.write(Data("\(error)\n".utf8))
    exit(1)
}
