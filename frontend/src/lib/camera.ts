import { Camera, CameraResultType, CameraSource } from '@capacitor/camera';

/**
 * Opens the device camera (native Android/iOS) and returns the captured photo
 * as a File ready for upload. On Android the CAMERA permission dialog is
 * requested automatically by the Capacitor Camera plugin on first use.
 *
 * `CameraSource.Prompt` shows an action sheet: "Camera" / "Gallery", so the
 * user can also pick an existing photo.
 *
 * On the web this falls back to the browser file picker / getUserMedia
 * implementation provided by the Capacitor web runtime.
 */
export async function takePhoto(): Promise<File | null> {
  const photo = await Camera.getPhoto({
    resultType: CameraResultType.Uri,
    source: CameraSource.Prompt,
    quality: 85,
    width: 1280,
    correctOrientation: true,
  });
  if (!photo.webPath) return null;
  const res = await fetch(photo.webPath);
  const blob = await res.blob();
  const ext = photo.format && photo.format !== 'unknown' ? photo.format : 'jpg';
  return new File([blob], `plant-photo-${Date.now()}.${ext}`, {
    type: blob.type || 'image/jpeg',
  });
}