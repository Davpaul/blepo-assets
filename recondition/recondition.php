<?php
/**
 * Plugin Name: Recondition
 * Description: A light 12 week gym plan with session tracking, spoken cues and a splits finisher. Add [recondition] to any page.
 * Version: 1.0.0
 * License: GPLv2 or later
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'RC_VER', '1.0.0' );

function rc_pose_keys() {
	return array(
		'lunge'      => 'Low lunge',
		'halfsplit'  => 'Half split',
		'butterfly'  => 'Butterfly',
		'straddle'   => 'Straddle',
		'frontsplit' => 'Front split slide',
	);
}

add_shortcode( 'recondition', function () {
	$url = plugin_dir_url( __FILE__ );
	wp_enqueue_style( 'recondition', $url . 'assets/app.css', array(), RC_VER );
	wp_enqueue_script( 'recondition', $url . 'assets/app.js', array(), RC_VER, true );
	wp_localize_script( 'recondition', 'RC_CFG', array(
		'rest'     => esc_url_raw( rest_url( 'recondition/v1/state' ) ),
		'nonce'    => wp_create_nonce( 'wp_rest' ),
		'loggedIn' => is_user_logged_in(),
		'photos'   => (object) get_option( 'rc_photos', array() ),
	) );
	return '<div id="recondition-app" class="rc-root"><noscript>Recondition needs JavaScript.</noscript></div>';
} );

add_action( 'rest_api_init', function () {
	register_rest_route( 'recondition/v1', '/state', array(
		array(
			'methods'             => 'GET',
			'permission_callback' => 'is_user_logged_in',
			'callback'            => function () {
				$raw = get_user_meta( get_current_user_id(), 'rc_state', true );
				$obj = $raw ? json_decode( $raw, true ) : null;
				return rest_ensure_response( $obj ? $obj : (object) array() );
			},
		),
		array(
			'methods'             => 'POST',
			'permission_callback' => 'is_user_logged_in',
			'callback'            => function ( WP_REST_Request $req ) {
				$body = $req->get_body();
				if ( strlen( $body ) > 400000 ) {
					return new WP_Error( 'rc_big', 'Too large', array( 'status' => 413 ) );
				}
				$data = json_decode( $body, true );
				if ( ! is_array( $data ) || ! isset( $data['v'] ) ) {
					return new WP_Error( 'rc_bad', 'Bad data', array( 'status' => 400 ) );
				}
				update_user_meta( get_current_user_id(), 'rc_state', wp_slash( wp_json_encode( $data ) ) );
				return rest_ensure_response( array( 'ok' => true ) );
			},
		),
	) );
} );

add_action( 'admin_menu', function () {
	add_options_page( 'Recondition', 'Recondition', 'manage_options', 'recondition', 'rc_settings_page' );
} );

add_action( 'admin_init', function () {
	register_setting( 'rc_group', 'rc_photos', array(
		'type'              => 'array',
		'sanitize_callback' => function ( $in ) {
			$out = array();
			foreach ( array_keys( rc_pose_keys() ) as $k ) {
				if ( ! empty( $in[ $k ] ) ) {
					$out[ $k ] = esc_url_raw( $in[ $k ] );
				}
			}
			return $out;
		},
	) );
} );

function rc_settings_page() {
	$photos = get_option( 'rc_photos', array() );
	?>
	<div class="wrap">
		<h1>Recondition</h1>
		<p>Put <code>[recondition]</code> on any page. The splits finisher shows a built in diagram for each pose. To show a photo instead, paste an image URL from your Media Library below.</p>
		<form method="post" action="options.php">
			<?php settings_fields( 'rc_group' ); ?>
			<table class="form-table">
				<?php foreach ( rc_pose_keys() as $k => $label ) : ?>
					<tr>
						<th><label for="rc_<?php echo esc_attr( $k ); ?>"><?php echo esc_html( $label ); ?></label></th>
						<td><input type="url" class="regular-text" id="rc_<?php echo esc_attr( $k ); ?>" name="rc_photos[<?php echo esc_attr( $k ); ?>]" value="<?php echo esc_attr( $photos[ $k ] ?? '' ); ?>" placeholder="https://"></td>
					</tr>
				<?php endforeach; ?>
			</table>
			<?php submit_button(); ?>
		</form>
	</div>
	<?php
}
