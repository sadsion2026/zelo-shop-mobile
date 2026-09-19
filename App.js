import React, { useRef } from 'react';
import { 
  StyleSheet, 
  View, 
  StatusBar, 
  SafeAreaView, 
  Platform 
} from 'react-native';
import { WebView } from 'react-native-webview';
import bundle from './bundle.json';

export default function App() {
  const webViewRef = useRef(null);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#FAFAFC" />
      <WebView
        ref={webViewRef}
        originWhitelist={['*']}
        source={{ 
          html: bundle.html,
          baseUrl: 'https://zeloshop.local' 
        }}
        style={styles.webview}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        allowFileAccess={true}
        allowUniversalAccessFromFileURLs={true}
        allowsInlineMediaPlayback={true}
        scalesPageToFit={false}
        bounces={false}
        scrollEnabled={true}
        showsVerticalScrollIndicator={false}
        showsHorizontalScrollIndicator={false}
        mixedContentMode="always"
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAFAFC',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  webview: {
    flex: 1,
    backgroundColor: '#FAFAFC',
  },
});
