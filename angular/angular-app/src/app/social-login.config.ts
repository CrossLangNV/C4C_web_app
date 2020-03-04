import {
  SocialLoginModule,
  AuthServiceConfig,
  GoogleLoginProvider
} from 'angularx-social-login';
import { Environment } from 'src/environments/environment-variables';

export function getAuthServiceConfigs() {
  let config = new AuthServiceConfig([
    {
      id: GoogleLoginProvider.PROVIDER_ID,
      provider: new GoogleLoginProvider(Environment.ANGULAR_GOOGLE_CLIENT_ID)
    }
  ]);

  return config;
}
