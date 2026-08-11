/*
 * Release configuration
 *
 * Release identity is loaded from ../RELEASE.json. The release build also
 * creates release-data.js as a file:// fallback. Neither file may contain the
 * release ZIP checksum; that value belongs only in the external pastor message.
 */
window.PASTOR_SETUP_CONFIG = Object.freeze({
  releaseMetadataUrl: "../RELEASE.json",
  chatgptUrl: "https://chatgpt.com/",
  pluginName: "Pastor Assistant Agent OS",
  pluginVersion: "0.2.0"
});
